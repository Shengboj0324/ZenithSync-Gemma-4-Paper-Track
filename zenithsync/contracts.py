"""Pure contracts; no model, tool execution, or evaluator outcomes are invented."""

from dataclasses import dataclass, replace
from enum import Enum


def natural(value: int, name: str) -> int:
    """Reject bools and coercions: accounting is in exact nonnegative integers."""
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        c not in "0123456789abcdef" for c in value
    ):
        raise ValueError("expected lowercase SHA-256 hex digest")
    return value


@dataclass(frozen=True)
class Budget:
    """Charged durations supplied by the runner; not a wall-clock watchdog.

    Overruns remain visible as debt. Admission is a deterministic constraint,
    not a prediction that an action will finish within its requested duration.
    """

    limit_ns: int
    reserve_ns: int
    charged_ns: int = 0

    def __post_init__(self) -> None:
        for name in ("limit_ns", "reserve_ns", "charged_ns"):
            natural(getattr(self, name), name)
        if self.reserve_ns > self.limit_ns:
            raise ValueError("reserve exceeds limit")

    @property
    def available_ns(self) -> int:
        return max(0, self.limit_ns - self.reserve_ns - self.charged_ns)

    @property
    def overrun_ns(self) -> int:
        return max(0, self.charged_ns - self.limit_ns)

    def admits(self, requested_ns: int) -> bool:
        natural(requested_ns, "requested_ns")
        return self.charged_ns + self.reserve_ns + requested_ns <= self.limit_ns

    def charge(self, elapsed_ns: int) -> "Budget":
        natural(elapsed_ns, "elapsed_ns")
        return replace(self, charged_ns=self.charged_ns + elapsed_ns)


def context_fits(*, input_tokens: int, output_tokens: int,
                 protocol_tokens: int, limit_tokens: int) -> bool:
    """Counts must come from the pinned tokenizer, never a character heuristic."""
    values = (input_tokens, output_tokens, protocol_tokens, limit_tokens)
    for value in values:
        natural(value, "token count")
    return sum(values[:3]) <= limit_tokens


class Phase(str, Enum):
    READY = "ready"
    WORKING = "working"
    SUBMITTED = "submitted"
    STOPPED = "stopped"


class Kind(str, Enum):
    START = "start"
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    CANDIDATE = "candidate"
    CHECK = "check"
    SUBMIT = "submit"
    STOP = "stop"


@dataclass(frozen=True)
class Event:
    """A versioned event references retained bytes by hash, not mutable paths.

    Candidate hashes identify the complete test input bundle (tree, test suite,
    and environment specification), not merely the textual patch. A receipt
    hash identifies the runner's observed check output; it is not an oracle.
    """

    sequence: int
    kind: Kind
    artifact_sha256: str | None = None
    candidate_sha256: str | None = None
    passed: bool | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        natural(self.sequence, "sequence")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported event schema")
        if not isinstance(self.kind, Kind):
            raise ValueError("kind must be a Kind enum")
        for value in (self.artifact_sha256, self.candidate_sha256):
            if value is not None:
                digest(value)
        if self.passed is not None and type(self.passed) is not bool:
            raise ValueError("passed must be boolean or null")
        requirements = {
            Kind.START: (False, False, False),
            Kind.OBSERVATION: (True, False, False),
            Kind.HYPOTHESIS: (True, False, False),
            Kind.CANDIDATE: (False, True, False),
            Kind.CHECK: (True, True, True),
            Kind.SUBMIT: (True, True, False),
            Kind.STOP: (True, False, False),
        }
        present = tuple(x is not None for x in (
            self.artifact_sha256, self.candidate_sha256, self.passed
        ))
        if present != requirements[self.kind]:
            raise ValueError("invalid fields for event kind")


@dataclass(frozen=True)
class TaskState:
    phase: Phase = Phase.READY
    next_sequence: int = 0
    candidate_sha256: str | None = None
    check_receipt_sha256: str | None = None
    check_passed: bool | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.phase, Phase):
            raise ValueError("phase must be a Phase enum")
        natural(self.next_sequence, "next_sequence")
        for value in (self.candidate_sha256, self.check_receipt_sha256):
            if value is not None:
                digest(value)
        if self.check_passed is not None and type(self.check_passed) is not bool:
            raise ValueError("check_passed must be boolean or null")
        if (self.check_passed is None) != (self.check_receipt_sha256 is None):
            raise ValueError("check result and receipt must be present together")
        if self.check_receipt_sha256 is not None and self.candidate_sha256 is None:
            raise ValueError("check requires a candidate")
        if self.phase == Phase.READY:
            if self.next_sequence != 0 or self.candidate_sha256 is not None:
                raise ValueError("ready state must be empty")
        elif self.next_sequence == 0:
            raise ValueError("noninitial state requires an event")
        if self.phase == Phase.SUBMITTED and self.candidate_sha256 is None:
            raise ValueError("submission requires a candidate")

    def apply(self, event: Event) -> "TaskState":
        if not isinstance(event, Event):
            raise ValueError("expected an Event")
        if event.sequence != self.next_sequence:
            raise ValueError("event sequence gap or duplicate")
        if self.phase in (Phase.SUBMITTED, Phase.STOPPED):
            raise ValueError("terminal task cannot accept events")
        changes = {"next_sequence": self.next_sequence + 1}
        if event.kind == Kind.STOP:
            changes["phase"] = Phase.STOPPED
        elif self.phase == Phase.READY:
            if event.kind != Kind.START:
                raise ValueError("task must start before work")
            changes["phase"] = Phase.WORKING
        elif event.kind == Kind.START:
            raise ValueError("task already started")
        elif event.kind == Kind.CANDIDATE:
            changes.update(candidate_sha256=event.candidate_sha256,
                           check_receipt_sha256=None, check_passed=None)
        elif event.kind in (Kind.CHECK, Kind.SUBMIT):
            if self.candidate_sha256 != event.candidate_sha256:
                raise ValueError("receipt refers to a stale or unknown candidate")
            if event.kind == Kind.CHECK:
                changes.update(check_receipt_sha256=event.artifact_sha256,
                               check_passed=event.passed)
            else:
                # Submission is permitted even without passing local checks.
                # Only the independent evaluator can declare repair acceptance.
                changes["phase"] = Phase.SUBMITTED
        return replace(self, **changes)


def replay(events: list[Event]) -> TaskState:
    state = TaskState()
    for event in events:
        state = state.apply(event)
    return state
