"""Test-only conformance verifier for the E4 logical record stream."""

import json
from pathlib import Path

import pytest

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "e4_storage_v1.json").read_text(
        encoding="utf-8"
    )
)
FIELDS = {
    "assignment": ("enrollment", "protocol", "sequence"),
    "allocation": ("enrollment", "arm"),
    "visit": ("id", "enrollment", "phase", "form"),
    "slot": ("id", "visit", "ordinal", "item", "scorer"),
    "exposure": ("enrollment", "activity", "active_ms", "examples"),
    "attempt": ("id", "slot", "response", "latency_ms"),
    "outcome": ("slot", "status", "attempt"),
    "close_visit": ("visit", "status"),
    "withdrawal": ("enrollment",),
}
INTEGER_FIELDS = {"ordinal", "active_ms", "examples", "latency_ms"}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


class _Ledger:
    def __init__(self):
        self.records = {kind: {} for kind in FIELDS}
        self.visits_by_phase = {}
        self.slots_by_visit = {}
        self.attempts_by_slot = {}

    def _enrollment_of_slot(self, slot):
        visit = self.records["slot"][slot]["visit"]
        return self.records["visit"][visit]["enrollment"]

    def accept(self, record):
        kind = record["kind"]
        fields = FIELDS[kind]
        assert set(record) == {"version", "kind", *fields}, "record fields"
        assert type(record["version"]) is int and record["version"] == 1, "version"
        for field in fields:
            value = record[field]
            if field in INTEGER_FIELDS:
                assert type(value) is int and value >= 0, "nonnegative integer"
            elif field != "response" and not (kind == "outcome" and field == "attempt"):
                assert _nonempty(value), "nonempty identifier"

        key = record[fields[0]]
        existing = self.records[kind].get(key)
        if existing is not None:
            # JSON equality distinguishes booleans from numbers.
            assert json.dumps(existing, sort_keys=True) == json.dumps(
                record, sort_keys=True
            ), "conflicting retry"
            return "retry"

        getattr(self, f"_{kind}")(record)
        self.records[kind][key] = record
        return "accepted"

    def _protocol(self, enrollment):
        assignment = self.records["assignment"][enrollment]
        return FIXTURE["protocols"][assignment["protocol"]]

    def _assignment(self, record):
        protocol = FIXTURE["protocols"][record["protocol"]]
        assert record["sequence"] in protocol["sequences"], "unknown sequence"

    def _allocation(self, record):
        enrollment = record["enrollment"]
        assert record["arm"] in self._protocol(enrollment)["arms"], "unknown arm"
        baseline = self.visits_by_phase.get((enrollment, "baseline"))
        assert baseline in self.records["close_visit"], "baseline still open"

    def _visit(self, record):
        enrollment = record["enrollment"]
        phase = record["phase"]
        assignment = self.records["assignment"][enrollment]
        sequence = self._protocol(enrollment)["sequences"][assignment["sequence"]]
        assert sequence.get(phase) == record["form"], "form assignment mismatch"
        key = (enrollment, phase)
        assert key not in self.visits_by_phase, "duplicate visit phase"
        if phase != "baseline":
            assert enrollment in self.records["allocation"], "missing allocation"
        self.visits_by_phase[key] = record["id"]
        self.slots_by_visit[record["id"]] = {}

    def _slot(self, record):
        visit_id = record["visit"]
        visit = self.records["visit"][visit_id]
        assert visit_id not in self.records["close_visit"], "closed visit"
        slots = self.slots_by_visit[visit_id]
        ordinal = record["ordinal"]
        assert ordinal not in slots, "duplicate slot ordinal"
        items = FIXTURE["forms"][visit["form"]]
        assert ordinal < len(items) and items[ordinal] == record["item"], (
            "item mismatch"
        )
        assert FIXTURE["items"][record["item"]] == record["scorer"], "scorer mismatch"
        slots[ordinal] = record["id"]

    def _exposure(self, record):
        enrollment = record["enrollment"]
        assert enrollment in self.records["allocation"], "missing allocation"
        assert record["activity"] in self._protocol(enrollment)["activities"], (
            "unknown activity"
        )

    def _attempt(self, record):
        slot = record["slot"]
        self.records["slot"][slot]
        assert self._enrollment_of_slot(slot) not in self.records["withdrawal"], (
            "withdrawn enrollment"
        )
        assert slot not in self.records["outcome"], "terminal slot"
        assert slot not in self.attempts_by_slot, "duplicate attempt"
        response = record["response"]
        assert (
            isinstance(response, list)
            and len(response) == 4
            and all(
                type(value) is int and -(2**31) <= value < 2**31 for value in response
            )
        ), "invalid response"
        self.attempts_by_slot[slot] = record["id"]

    def _outcome(self, record):
        slot = record["slot"]
        self.records["slot"][slot]
        status = record["status"]
        attempt = self.attempts_by_slot.get(slot)
        if status == "submitted":
            assert attempt is not None and record["attempt"] == attempt, "attempt link"
        else:
            assert status in {"invalid", "unpresented", "interrupted"}, "slot status"
            assert attempt is None and record["attempt"] is None, "unexpected attempt"

    def _close_visit(self, record):
        visit = record["visit"]
        form = self.records["visit"][visit]["form"]
        slots = self.slots_by_visit[visit]
        assert len(slots) == len(FIXTURE["forms"][form]), "incomplete slot assignment"
        outcomes = self.records["outcome"]
        assert all(slot in outcomes for slot in slots.values()), "missing outcome"
        allowed = {
            "completed": {"submitted", "invalid"},
            "expired": {"unpresented"},
            "interrupted": {"submitted", "invalid", "interrupted", "unpresented"},
            "withdrawn": {"submitted", "invalid", "interrupted", "unpresented"},
        }
        if record["status"] == "withdrawn":
            enrollment = self.records["visit"][visit]["enrollment"]
            assert enrollment in self.records["withdrawal"], "withdrawal missing"
        statuses = {outcomes[slot]["status"] for slot in slots.values()}
        assert statuses <= allowed[record["status"]], "visit outcome mismatch"

    def _withdrawal(self, record):
        assert record["enrollment"] in self.records["assignment"], "unknown enrollment"


def _load(records):
    ledger = _Ledger()
    for record in records:
        ledger.accept(record)
    return ledger


def test_e4_reconstructs_assigned_visits_and_missingness():
    ledger = _load(FIXTURE["records"])
    assert {
        visit: {
            "status": ledger.records["close_visit"].get(visit, {}).get("status"),
            "slots": [
                ledger.records["outcome"].get(slot, {}).get("status")
                for _, slot in sorted(slots.items())
            ],
        }
        for visit, slots in ledger.slots_by_visit.items()
    } == FIXTURE["expected_visits"]
    assert ledger.accept(FIXTURE["records"][4]) == "retry"
    ledger.accept(FIXTURE["records"][4])
    assert len(ledger.records["attempt"]) == 2


@pytest.mark.parametrize("case", FIXTURE["rejections"], ids=lambda case: case["name"])
def test_e4_rejects_nonconforming_records(case):
    ledger = _load(FIXTURE["records"][: case["after"]])
    with pytest.raises((AssertionError, KeyError), match=case["error"]):
        ledger.accept(case["record"])


def _record(kind, **fields):
    return {"version": 1, "kind": kind, **fields}


def test_e4_withdrawal_closes_open_visit_as_withdrawn():
    ledger = _load(FIXTURE["records"][:15])
    ledger.accept(_record("outcome", slot="b2", status="interrupted", attempt=None))
    with pytest.raises(AssertionError, match="withdrawal missing"):
        ledger.accept(_record("close_visit", visit="post", status="withdrawn"))
    ledger.accept(_record("withdrawal", enrollment="synthetic-1"))
    ledger.accept(_record("close_visit", visit="post", status="withdrawn"))
    assert ledger.records["close_visit"]["post"]["status"] == "withdrawn"


def test_e4_rejects_attempts_after_withdrawal():
    ledger = _load(FIXTURE["records"][:13])
    ledger.accept(_record("withdrawal", enrollment="synthetic-1"))
    with pytest.raises(AssertionError, match="withdrawn enrollment"):
        ledger.accept(
            _record(
                "attempt", id="late", slot="b2", response=[0, 0, 0, 1], latency_ms=5
            )
        )
