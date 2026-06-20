from __future__ import annotations

import json
from subprocess import CompletedProcess

import tools.migration.trace_metadata_identity_digest_parity as parity


def test_python_oracle_cases_are_deterministic() -> None:
    cases = parity.python_oracle_cases()
    assert [case.name for case in cases] == [
        "plain-2d-minimal",
        "plain-3d-minimal",
        "wrapped-4d-minimal",
    ]
    assert cases == parity.python_oracle_cases()


def test_python_oracle_identity_and_digest_are_exact() -> None:
    first_case = parity.python_oracle_cases()[0]
    assert first_case.identity == (
        '{"dimension":2,"mode":"2d","schema_version":1,"topology":"plain","trace_id":"plain_2d_spawn_001"}'
    )
    assert first_case.digest == "d22dcee65766b3ac75cc129b41c330762bec3b015c6638def83073cf4f51ab06"


def test_compare_cases_detects_identity_and_digest_mismatch() -> None:
    native_cases = [
        {
            "name": "plain-2d-minimal",
            "identity": '{"dimension":2,"mode":"2d","schema_version":1,"topology":"plain","trace_id":"plain_2d_spawn_001"}',
            "digest": "0000000000000000000000000000000000000000000000000000000000000000",
        }
    ]

    failures = parity.compare_cases(native_cases)

    assert any("digest mismatch" in failure for failure in failures)


def test_load_native_cases_parses_native_parity_output(monkeypatch) -> None:
    payload = {
        "cases": [
            {
                "name": "plain-2d-minimal",
                "identity": '{"dimension":2,"mode":"2d","schema_version":1,"topology":"plain","trace_id":"plain_2d_spawn_001"}',
                "digest": "d22dcee65766b3ac75cc129b41c330762bec3b015c6638def83073cf4f51ab06",
            },
            {
                "name": "plain-3d-minimal",
                "identity": '{"dimension":3,"mode":"3d","schema_version":1,"topology":"plain","trace_id":"plain_3d_spawn_001"}',
                "digest": "47e2d813e92ed082dfd5680d02ceb85c5b44abeaa0fc745c8acf40dc07566575",
            },
            {
                "name": "wrapped-4d-minimal",
                "identity": '{"dimension":4,"mode":"4d","schema_version":1,"topology":"wrapped","trace_id":"wrapped_4d_spawn_001"}',
                "digest": "0d818fc7a85edc265fc2dbedb9aea0a5b36678a3843014fc66902e4650beb648",
            },
        ]
    }

    def fake_run(*args, **kwargs):
        return CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(parity.subprocess, "run", fake_run)

    native_cases = parity.load_native_cases(["native"])

    assert native_cases == payload["cases"]


def test_run_reports_advisory_when_native_unavailable_in_default_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        parity,
        "load_native_cases",
        lambda command=None: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = parity.run(strict=False)

    assert result.failures == []
    assert result.advisories
    assert any("TET4D_STRICT_PARITY=1" in advisory for advisory in result.advisories)


def test_run_fails_when_native_unavailable_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        parity,
        "load_native_cases",
        lambda command=None: (_ for _ in ()).throw(RuntimeError("compiler missing")),
    )

    result = parity.run(strict=True)

    assert result.advisories == []
    assert any("compiler missing" in failure for failure in result.failures)
