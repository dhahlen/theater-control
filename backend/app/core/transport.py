"""Async line-oriented TCP transport with automatic reconnect.

Shared by the raw-socket adapters (Trinnov, Kaleidescape, MadVR). It owns a
persistent connection, exposes a coroutine to send a line, and pushes every
received line to a callback so adapters can parse asynchronous status
broadcasts. A background reader task reconnects with backoff when the link
drops, since these panels are the most-used surfaces in the UI.

The transport is deliberately dumb about protocol: it knows only about a line
terminator and bytes. Adapters own framing and parsing.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

log = logging.getLogger("theater.transport")

LineHandler = Callable[[str], Awaitable[None] | None]
ConnectHook = Callable[[], Awaitable[None]]


class LineTransport:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        on_line: LineHandler,
        on_connect: ConnectHook | None = None,
        terminator: bytes = b"\n",
        connect_timeout: float = 5.0,
        reconnect_min_s: float = 1.0,
        reconnect_max_s: float = 30.0,
    ) -> None:
        self._host = host
        self._port = port
        self._on_line = on_line
        self._on_connect = on_connect
        self._terminator = terminator
        self._connect_timeout = connect_timeout
        self._reconnect_min_s = reconnect_min_s
        self._reconnect_max_s = reconnect_max_s

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._task: asyncio.Task[None] | None = None
        self._connected = asyncio.Event()
        self._closing = False
        self._write_lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    async def start(self) -> None:
        """Start the connect/read loop and wait briefly for the first connect."""

        if self._task is None:
            self._closing = False
            self._task = asyncio.create_task(self._run(), name=f"transport:{self._host}")
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=self._connect_timeout)
        except asyncio.TimeoutError:
            # Not fatal: the loop keeps retrying in the background and the device
            # simply reads as offline until it connects.
            log.warning("initial connect to %s:%s timed out", self._host, self._port)

    async def stop(self) -> None:
        self._closing = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._close_streams()

    async def send_line(self, line: str) -> None:
        """Send one line, appending the terminator. Raises if not connected."""

        writer = self._writer
        if writer is None or not self._connected.is_set():
            raise ConnectionError(f"{self._host}:{self._port} not connected")
        data = line.encode() + self._terminator
        async with self._write_lock:
            writer.write(data)
            await writer.drain()

    async def _run(self) -> None:
        backoff = self._reconnect_min_s
        while not self._closing:
            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self._host, self._port),
                    timeout=self._connect_timeout,
                )
                backoff = self._reconnect_min_s
                self._connected.set()
                log.info("connected to %s:%s", self._host, self._port)
                if self._on_connect:
                    await self._on_connect()
                await self._read_loop()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.debug("connection to %s:%s failed: %s", self._host, self._port, exc)
            finally:
                self._connected.clear()
                await self._close_streams()
            if self._closing:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._reconnect_max_s)

    async def _read_loop(self) -> None:
        assert self._reader is not None
        while not self._closing:
            raw = await self._reader.readline()
            if raw == b"":
                raise ConnectionError("connection closed by peer")
            line = raw.decode(errors="replace").rstrip("\r\n")
            if not line:
                continue
            result = self._on_line(line)
            if asyncio.iscoroutine(result):
                await result

    async def _close_streams(self) -> None:
        writer, self._writer, self._reader = self._writer, None, None
        if writer is not None:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
