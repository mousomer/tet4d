from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tet4d.engine.runtime import score_analyzer
from tet4d.engine.runtime.score_analyzer import (
    analyze_lock_event,
    hud_analysis_lines,
    record_score_analysis_event,
    reset_score_analyzer_runtime_state,
    score_analysis_summary_snapshot,
    score_analyzer_logging_enabled,
    validate_score_analysis_event,
    validate_score_analysis_summary,
)


class TestScoreAnalyzer(unittest.TestCase):
    def _sample_event(
        self, *, seq: int = 1, session_id: str = "test-session"
    ) -> dict[str, object]:
        board_pre = {(0, 3): 1, (1, 3): 1}
        board_post = {(0, 3): 1, (1, 3): 1, (2, 3): 1, (3, 3): 1}
        return analyze_lock_event(
            board_pre=board_pre,
            board_post=board_post,
            dims=(4, 4),
            gravity_axis=1,
            locked_cells=((2, 3), (3, 3)),
            cleared=1,
            piece_id="domino",
            actor_mode="human",
            bot_mode="off",
            grid_mode="full",
            speed_level=3,
            raw_points=45,
            final_points=45,
            session_id=session_id,
            seq=seq,
        )

    def test_analyze_lock_event_returns_expected_shape(self) -> None:
        event = self._sample_event()

        self.assertEqual(event["session_id"], "test-session")
        self.assertEqual(event["seq"], 1)
        self.assertEqual(event["dimension"], 2)
        self.assertIn("board_pre", event)
        self.assertIn("board_post", event)
        self.assertIn("placement", event)
        self.assertIn("delta", event)
        self.assertIn("board_health_score", event)
        self.assertIn("placement_quality_score", event)
        self.assertGreaterEqual(float(event["board_health_score"]), 0.0)
        self.assertLessEqual(float(event["board_health_score"]), 1.0)
        self.assertGreaterEqual(float(event["placement_quality_score"]), 0.0)
        self.assertLessEqual(float(event["placement_quality_score"]), 1.0)
        ok_event, msg_event = validate_score_analysis_event(event)
        self.assertTrue(ok_event, msg_event)

    def test_hud_lines(self) -> None:
        lines = hud_analysis_lines(
            {
                "placement_quality_score": 0.72,
                "board_health_score": 0.64,
                "delta": {
                    "holes_count_norm": -0.03,
                    "near_complete_planes_norm": 0.02,
                    "top_zone_risk_norm": -0.01,
                },
            }
        )
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("Quality: "))
        self.assertTrue(lines[1].startswith("Board health: "))
        self.assertTrue(lines[2].startswith("Trend: "))

    def test_validate_summary_contract(self) -> None:
        summary = score_analysis_summary_snapshot()
        ok, msg = validate_score_analysis_summary(summary)
        self.assertTrue(ok, msg)

    def test_record_event_writes_event_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_path = tmp_path / "score_analyzer.json"
            events_path = tmp_path / "state" / "events.jsonl"
            summary_path = tmp_path / "state" / "summary.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "enabled": True,
                        "logging": {
                            "enabled": True,
                            "events_file": "state/events.jsonl",
                            "summary_file": "state/summary.json",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(score_analyzer, "_ROOT_DIR", tmp_path),
                mock.patch.object(score_analyzer, "_CONFIG_PATH", config_path),
            ):
                reset_score_analyzer_runtime_state()
                self.assertTrue(score_analyzer_logging_enabled())

                first = self._sample_event(seq=1, session_id="session-a")
                second = self._sample_event(seq=2, session_id="session-a")
                record_score_analysis_event(first)
                record_score_analysis_event(second)

                lines = events_path.read_text(encoding="utf-8").strip().splitlines()
                self.assertEqual(len(lines), 2)
                first_logged = json.loads(lines[0])
                self.assertEqual(first_logged["session_id"], "session-a")
                self.assertEqual(first_logged["seq"], 1)

                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                ok, msg = validate_score_analysis_summary(summary)
                self.assertTrue(ok, msg)
                self.assertEqual(summary["totals"]["events"], 2)
                self.assertEqual(summary["sessions"]["session-a"]["events"], 2)
            reset_score_analyzer_runtime_state()

    def test_record_event_sanitizes_output_paths_to_state_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_path = tmp_path / "score_analyzer.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "enabled": True,
                        "logging": {
                            "enabled": True,
                            "events_file": "../../outside/events.jsonl",
                            "summary_file": "/tmp/outside/summary.json",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(score_analyzer, "_ROOT_DIR", tmp_path),
                mock.patch.object(score_analyzer, "_CONFIG_PATH", config_path),
            ):
                reset_score_analyzer_runtime_state()
                record_score_analysis_event(
                    self._sample_event(seq=1, session_id="sanitized")
                )

                safe_events = tmp_path / "state" / "analytics" / "score_events.jsonl"
                safe_summary = tmp_path / "state" / "analytics" / "score_summary.json"
                self.assertTrue(safe_events.exists())
                self.assertTrue(safe_summary.exists())
                self.assertFalse(
                    (tmp_path.parent / "outside" / "events.jsonl").exists()
                )

            reset_score_analyzer_runtime_state()


if __name__ == "__main__":
    unittest.main()
