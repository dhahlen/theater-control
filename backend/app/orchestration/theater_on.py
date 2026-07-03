"""Theater On orchestration routine.

Implements the sequence, validation, and idempotency described in
docs/usecases/theater-on.md. Coordinates JVC, MadVR, and Trinnov adapters and
emits a progress event per step so the front end can render a live checklist.

Success requires the three JVC checks the user cares about: power ``on``, input
matches target, and low-latency matches target. MadVR and Trinnov steps are
best-effort and reported as ``sent_unconfirmed`` when the device does not
confirm state.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable

log = logging.getLogger("theater.theater_on")


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    SENT_UNCONFIRMED = "sent_unconfirmed"
    FAILED = "failed"


@dataclass
class StepResult:
    step: str
    status: StepStatus = StepStatus.PENDING
    detail: str = ""


@dataclass
class RoutineResult:
    overall: str = "pending"          # "success" | "partial" | "failed"
    steps: list[StepResult] = field(default_factory=list)


ProgressEmitter = Callable[[StepResult], Awaitable[None]]

JVC_WARMUP_TIMEOUT_S = 60.0
MADVR_WAKE_TIMEOUT_S = 20.0


class _Progress:
    """Accumulates step results and emits each transition to the UI."""

    def __init__(self, emit: ProgressEmitter) -> None:
        self._emit = emit
        self.steps: list[StepResult] = []

    async def start(self, step: str, detail: str = "") -> StepResult:
        result = StepResult(step=step, status=StepStatus.RUNNING, detail=detail)
        self.steps.append(result)
        await self._emit(result)
        return result

    async def finish(self, result: StepResult, status: StepStatus, detail: str = "") -> None:
        result.status = status
        if detail:
            result.detail = detail
        await self._emit(result)


async def run_theater_on(
    source: str,
    adapters: dict[str, Any],
    config: dict[str, Any],
    emit: ProgressEmitter,
) -> RoutineResult:
    """Execute the Theater On routine for the given source."""

    progress = _Progress(emit)
    behavior = _source_behavior(source, config)
    target_input = behavior["jvc_input"]
    target_low_latency = "on" if behavior["low_latency"] else "off"

    jvc = adapters.get("jvc")
    madvr = adapters.get("madvr")
    trinnov = adapters.get("trinnov")

    # Step: MadVR wake, in parallel with the JVC power sequence.
    madvr_task: asyncio.Task[None] | None = None
    if madvr is not None:
        madvr_step = await progress.start("madvr_wake", "Waking MadVR Envy")
        madvr_task = asyncio.create_task(_wake_madvr(madvr, progress, madvr_step))

    critical_ok = True

    # Steps 3-4: JVC power on + warm-up wait (skipped if already on).
    if jvc is None:
        step = await progress.start("jvc_power")
        await progress.finish(step, StepStatus.FAILED, "JVC adapter not configured")
        critical_ok = False
    else:
        powered = await _power_on_jvc(jvc, progress)
        critical_ok = critical_ok and powered

        if powered:
            # Step 5: input.
            input_ok = await _set_and_confirm(
                jvc, progress, "jvc_input", "input_mode",
                {"input": target_input}, lambda s: s.input, target_input,
            )
            # Step 6: low latency.
            latency_ok = await _set_and_confirm(
                jvc, progress, "jvc_low_latency", "low_latency",
                {"state": target_low_latency},
                lambda s: (s.extra or {}).get("low_latency"), target_low_latency,
            )
            # Step 7: picture mode (best-effort).
            await _set_picture_mode(jvc, progress, config)
            critical_ok = critical_ok and input_ok and latency_ok

    # Step 8: MadVR profile activation (best-effort).
    if madvr_task is not None:
        await madvr_task
    if madvr is not None:
        await _activate_madvr_profile(madvr, progress, source, config)

    # Step 9: Trinnov source + volume (best-effort).
    if trinnov is not None:
        await _prepare_trinnov(trinnov, progress, source, config)

    result = RoutineResult(steps=progress.steps)
    result.overall = _overall(progress.steps, critical_ok)
    return result


# -- step helpers --------------------------------------------------------


def _source_behavior(source: str, config: dict[str, Any]) -> dict[str, Any]:
    sources = config.get("sources") or {}
    behavior = sources.get(source)
    if behavior:
        return {"jvc_input": behavior.get("jvc_input", "hdmi1"),
                "low_latency": bool(behavior.get("low_latency", False))}
    jvc = config.get("jvc") or {}
    return {"jvc_input": jvc.get("target_input", "hdmi1"), "low_latency": False}


async def _wake_madvr(madvr: Any, progress: _Progress, step: StepResult) -> None:
    try:
        await madvr.send("wake", {})
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"wake failed: {exc}")
        return
    # Poll until the Envy answers, but never let it block the projector path.
    deadline = asyncio.get_event_loop().time() + MADVR_WAKE_TIMEOUT_S
    while asyncio.get_event_loop().time() < deadline:
        try:
            status = await madvr.get_status()
            if status.reachable.value == "online":
                await progress.finish(step, StepStatus.OK, "Envy is up")
                return
        except Exception:
            pass
        await asyncio.sleep(2.0)
    await progress.finish(step, StepStatus.SENT_UNCONFIRMED, "wake sent; not confirmed")


async def _power_on_jvc(jvc: Any, progress: _Progress) -> bool:
    step = await progress.start("jvc_power", "Powering projector")
    try:
        current = await jvc.read_power()
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"cannot reach JVC: {exc}")
        return False

    if current == "on":
        await progress.finish(step, StepStatus.OK, "already on")
        return True

    try:
        await jvc.send("power", {"state": "on"})
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"power command failed: {exc}")
        return False

    ok = await jvc.wait_until_power("on", timeout_s=JVC_WARMUP_TIMEOUT_S)
    if ok:
        await progress.finish(step, StepStatus.OK, "projector on")
        return True
    await progress.finish(step, StepStatus.FAILED, "projector did not reach 'on' before timeout")
    return False


async def _set_and_confirm(
    jvc: Any,
    progress: _Progress,
    step_name: str,
    command: str,
    params: dict[str, Any],
    read: Callable[[Any], Any],
    target: Any,
) -> bool:
    step = await progress.start(step_name, f"Setting {command} -> {target}")
    try:
        await jvc.send(command, params)
        status = await jvc.get_status()
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"{command} failed: {exc}")
        return False
    actual = read(status)
    if actual == target:
        await progress.finish(step, StepStatus.OK, f"confirmed {target}")
        return True
    await progress.finish(step, StepStatus.FAILED, f"expected {target}, read {actual}")
    return False


async def _set_picture_mode(jvc: Any, progress: _Progress, config: dict[str, Any]) -> None:
    mode = (config.get("jvc") or {}).get("target_picture_mode")
    if not mode:
        return
    step = await progress.start("jvc_picture_mode", f"Setting picture mode -> {mode}")
    try:
        await jvc.send("picture_mode", {"mode": mode})
        await progress.finish(step, StepStatus.SENT_UNCONFIRMED, f"sent {mode} (best-effort)")
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"picture mode failed: {exc}")


async def _activate_madvr_profile(
    madvr: Any, progress: _Progress, source: str, config: dict[str, Any]
) -> None:
    profiles = (config.get("madvr") or {}).get("profiles") or {}
    profile = profiles.get(source)
    step = await progress.start("madvr_profile", "Activating MadVR profile")
    if not profile:
        # Recommended default: the Envy applies automatic profiles by signal.
        await progress.finish(
            step, StepStatus.SENT_UNCONFIRMED, "auto profile (Envy signal-driven)"
        )
        return
    try:
        await madvr.send("restore_settings", {"target": str(profile)})
        await progress.finish(step, StepStatus.SENT_UNCONFIRMED, f"restored {profile}")
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"profile activation failed: {exc}")


async def _prepare_trinnov(
    trinnov: Any, progress: _Progress, source: str, config: dict[str, Any]
) -> None:
    sources = (config.get("trinnov") or {}).get("sources") or {}
    step = await progress.start("trinnov_source", f"Selecting Trinnov source {source}")
    if source not in sources:
        await progress.finish(
            step, StepStatus.SENT_UNCONFIRMED, f"no Trinnov mapping for {source}"
        )
        return
    try:
        status = await trinnov.get_status()
        if status.input == source:
            await progress.finish(step, StepStatus.OK, "already selected")
            return
        await trinnov.send("source", {"name": source})
        confirm = await trinnov.get_status()
        if confirm.input == source:
            await progress.finish(step, StepStatus.OK, f"source {source}")
        else:
            await progress.finish(step, StepStatus.SENT_UNCONFIRMED, "selected; not confirmed")
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"source select failed: {exc}")


def _overall(steps: list[StepResult], critical_ok: bool) -> str:
    if not critical_ok:
        return "failed"
    if any(s.status == StepStatus.FAILED for s in steps):
        return "partial"
    return "success"
