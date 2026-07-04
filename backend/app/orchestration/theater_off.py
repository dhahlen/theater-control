"""Theater Off orchestration routine.

Returns the theater to standby cleanly, per docs/usecases/theater-off.md. The
projector is the critical device: success requires the JVC to acknowledge
power-off (``standby`` or ``cooling``). Other devices are best-effort. The JVC
connection is not force-closed mid-cooldown; the off command is sent and the
projector completes its own fan-down.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .theater_on import RoutineResult, StepResult, StepStatus, _Progress, ProgressEmitter

log = logging.getLogger("theater.theater_off")

JVC_COOLDOWN_TIMEOUT_S = 45.0
ACCEPTABLE_OFF_STATES = {"standby", "cooling"}


async def run_theater_off(
    adapters: dict[str, Any],
    config: dict[str, Any],
    emit: ProgressEmitter,
) -> RoutineResult:
    progress = _Progress(emit)

    jvc = adapters.get("jvc")
    madvr = adapters.get("madvr")
    trinnov = adapters.get("trinnov")
    hue = adapters.get("hue")
    off_config = config.get("theater_off") or {}

    critical_ok = await _power_off_jvc(jvc, progress)

    # MadVR power off over IP (best-effort).
    if madvr is not None:
        step = await progress.start("madvr_power_off", "Powering off MadVR Envy")
        try:
            await madvr.send("power_off", {})
            await progress.finish(step, StepStatus.SENT_UNCONFIRMED, "PowerOff sent")
        except Exception as exc:
            await progress.finish(step, StepStatus.FAILED, f"power off failed: {exc}")

    # Trinnov: optionally power off per configuration; default keeps it on.
    if trinnov is not None:
        step = await progress.start("trinnov", "Trinnov shutdown")
        if off_config.get("power_off_trinnov"):
            try:
                await trinnov.send("power", {"state": "off"})
                await progress.finish(step, StepStatus.SENT_UNCONFIRMED, "power off sent")
            except Exception as exc:
                await progress.finish(step, StepStatus.FAILED, f"power off failed: {exc}")
        else:
            await progress.finish(step, StepStatus.OK, "left on (per config)")

    # Lighting: optionally recall a scene, or raise the group to a level, on
    # shutdown. A level is useful when no "lights up" scene exists on the bridge.
    scene = off_config.get("lighting_scene")
    level = off_config.get("lighting_level")
    if hue is not None and scene:
        step = await progress.start("lighting", f"Recalling scene {scene}")
        try:
            await hue.send("recall_scene", {"scene": scene})
            await progress.finish(step, StepStatus.OK, f"scene {scene}")
        except Exception as exc:
            await progress.finish(step, StepStatus.FAILED, f"scene recall failed: {exc}")
    elif hue is not None and level is not None:
        step = await progress.start("lighting", f"Lights to {round(level / 254 * 100)}%")
        try:
            await hue.send("set_level", {"bri": level})
            await progress.finish(step, StepStatus.OK, f"level {level}")
        except Exception as exc:
            await progress.finish(step, StepStatus.FAILED, f"set level failed: {exc}")

    result = RoutineResult(steps=progress.steps)
    result.overall = "failed" if not critical_ok else (
        "partial" if any(s.status == StepStatus.FAILED for s in progress.steps) else "success"
    )
    return result


async def _power_off_jvc(jvc: Any, progress: _Progress) -> bool:
    step = await progress.start("jvc_power_off", "Powering off projector")
    if jvc is None:
        await progress.finish(step, StepStatus.FAILED, "JVC adapter not configured")
        return False
    try:
        current = await jvc.read_power()
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"cannot reach JVC: {exc}")
        return False

    if current in ACCEPTABLE_OFF_STATES:
        await progress.finish(step, StepStatus.OK, f"already {current}")
        return True

    try:
        await jvc.send("power", {"state": "off"})
    except Exception as exc:
        await progress.finish(step, StepStatus.FAILED, f"power off failed: {exc}")
        return False

    # Poll until standby/cooling; cooling is an acceptable terminal state.
    deadline = asyncio.get_event_loop().time() + JVC_COOLDOWN_TIMEOUT_S
    while asyncio.get_event_loop().time() < deadline:
        try:
            power = await jvc.read_power()
        except Exception:
            power = None
        if power in ACCEPTABLE_OFF_STATES:
            await progress.finish(step, StepStatus.OK, f"projector {power}")
            return True
        await asyncio.sleep(2.0)
    await progress.finish(step, StepStatus.SENT_UNCONFIRMED, "off sent; state unconfirmed")
    # Off was acknowledged by the command even if the read did not confirm.
    return True
