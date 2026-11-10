"""Transcribe reviewed JSON expectations into native test data; no movement solver.

The generated header is a build artifact, never an update to the approved fixture.
E3 executes its original cylinder profile and an explicitly labeled torus companion.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def array(values: list) -> str:
    return "{" + ",".join(str(value) for value in values) + "}"


def frame(value: dict) -> str:
    return "{" + array(value["permutation"]) + "," + array(value["signs"]) + "}"


def cells(rows: list[dict]) -> str:
    return (
        "{"
        + ",".join(
            "{"
            + f"{row['id']},{row['domain']},{{{array(row['coordinate'])}}},{frame(row['frame'])}"
            + "}"
            for row in rows
        )
        + "}"
    )


def profile(value: dict) -> str:
    seams = []
    for row in value["gluings"]:
        boundaries = [
            "{"
            + f"{'xyzw'.index(row[key]['axis'])},{json.dumps(row[key]['side'])}"
            + "}"
            for key in ("source", "target")
        ]
        seams.append(
            "{"
            + ",".join(
                [json.dumps(row["id"]), *boundaries, frame(row["transform"]), "true"]
            )
            + "}"
        )
    return (
        "{"
        + f"{value['schema_version']},{value['dimension']},{array(value['board_dimensions'])}"
        + ",{ "
        + ",".join(seams)
        + "}}"
    )


def export(source: Path, output: Path) -> None:
    raw = source.read_bytes()
    data = json.loads(raw)
    profiles = {row["id"]: row["payload"] for row in data["profiles"]}
    states = {row["id"]: row for row in data["states"]}
    lines = [
        "// Generated test data from transport_v1.json; do not edit.",
        f'inline constexpr const char* FIXTURE_SHA256 = "{hashlib.sha256(raw).hexdigest()}";',
        "std::vector<FixtureCase> reviewed_cases() {",
        "std::vector<FixtureCase> result;",
    ]
    selected = {
        "E1",
        "bounded_interior",
        "cylinder_wall",
        "cylinder_wrap",
        "E2",
        "E3",
        "E8_proposal",
        "E9",
        "torus_self",
    }
    for case in data["cases"]:
        if case["id"] not in selected:
            continue
        state = states[case["source_state_ref"]]
        topology = profiles[state["profile_ref"]]
        rest = (
            "{"
            + ",".join(
                "{" + f"{row['id']},{{{array(row['coordinate'])}}}" + "}"
                for row in state["rest_cells"]
            )
            + "}"
        )
        action = array([case["action"]["axis"], case["action"]["delta"]])
        lines += [
            "{",
            "FixtureCase f;",
            f"f.id = {json.dumps(case['id'])};",
            f"f.source = {{{json.dumps(state['version'])},{json.dumps(state['object_key']['namespace'])},{state['object_key']['ordinal']},{profile(topology)},{rest},{cells(state['cells'])}}};",
            f"f.revision = {state['revision']};",
            f"f.action = {action};",
            f"f.failure = {json.dumps(case['blocked_reason'])};",
            f"f.classification = PieceClassification::{case['classification']};",
            "f.target = f.source;",
        ]
        if case["candidate"]["present"]:
            assert case["inverse"]["source_ref"] == case["source_state_ref"]
            assert case["inverse"]["forward_action"] == case["action"]
            lines += [
                f"f.target.cells = {cells(case['candidate']['cells'])};",
                f"f.inverse_version = {json.dumps(case['inverse']['version'])};",
            ]
            for row, source_cell in zip(case["per_cell"], state["cells"], strict=True):
                seam = "std::nullopt"
                if row["crossing"]:
                    pair = set(row["crossing"])
                    seam_id = next(
                        s["id"]
                        for s in topology["gluings"]
                        if {s[k]["axis"] + s[k]["side"] for k in ("source", "target")}
                        == pair
                    )
                    seam = json.dumps(seam_id)
                lines.append(
                    "f.witnesses.push_back({"
                    + f"{row['id']},{{{array(source_cell['coordinate'])}}},{{{array(row['target'])}}},{frame(row['transport'])},{action},{array(row['reverse_step'])},{seam}"
                    + "});"
                )
        if case["id"] == "E3":
            lines += [
                "result.push_back(f);",
                'f.id = "E3_torus_companion";',
                f"f.source.profile = {profile(profiles['torus_2d'])};",
                "f.target.profile = f.source.profile;",
                'for (auto& w : f.witnesses) if (w.seam) w.seam = "seam_001";',
            ]
        lines += ["result.push_back(std::move(f));", "}"]
    lines += ["return result;", "}"]
    lifecycle = data["lifecycle"][0]
    lines += [
        f"const MoveStepQuery E8_INTERVENING = {array([lifecycle['intervening_action']['axis'], lifecycle['intervening_action']['delta']])};",
        f"const std::vector<PieceCell> E8_CURRENT = {cells(lifecycle['expected_current_cells'])};",
        f"constexpr std::int64_t E8_REVISION = {lifecycle['expected_revision']};",
        f"constexpr std::int64_t E8_ABA_REVISION = {lifecycle['after_intervening_inverse_revision']};",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export(Path(sys.argv[1]), Path(sys.argv[2]))
