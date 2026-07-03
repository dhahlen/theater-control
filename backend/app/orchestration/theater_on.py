"""Theater On orchestration routine (scaffold).

Implements the sequence, validation, and idempotency described in
docs/usecases/theater-on.md. Coordinates JVC, MadVR, and Trinnov adapters.
Emits progress events for the live UI checklist. Method body is left for the
implementing agent; the structure and contract are fixed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable


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


async def run_theater_on(
    source: str,
    adapters: dict[str, Any],
    config: dict[str, Any],
    emit: ProgressEmitter,
) -> RoutineResult:
    """Execute the Theater On routine for the given source.

    Sequence (see docs/usecases/theater-on.md):
      1. MadVR Wake-on-LAN (parallel with JVC power).
      2. JVC power on.
      3. Poll JVC power until "on" (emit progress each poll).
      4. Set + confirm JVC input.
      5. Set + confirm JVC low_latency (per source).
      6. Set JVC picture_mode (best-effort).
      7. Activate MadVR profile for source.
      8. Trinnov: power/select source/volume; read back.
      9. Validate: JVC power on, JVC input matches, JVC low_latency matches,
         Trinnov source matches. Success requires the three JVC checks.

    Idempotent: if JVC already "on", skip power/warm-up and only validate/correct.
    """
    raise NotImplementedError
