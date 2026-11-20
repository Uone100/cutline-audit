import subprocess
import sys
import unittest
from pathlib import Path
from cutline_audit import Cue, audit, project


class TestCutline(unittest.TestCase):
    def test_cue_crosses_gap_and_lands_twice(self):
        source = [Cue(500, 2500, "A", 1), Cue(1000, 2000, "removed", 2)]
        result = project(source, [(0, 1000), (2000, 3000)])
        self.assertEqual(result, [Cue(500, 1000, "A", 1, 1), Cue(1000, 1500, "A", 1, 2)])

    def test_reordered_segments(self):
        self.assertEqual(project([Cue(80, 90, "X", 1)], [(80, 90), (0, 10), (80, 90)]),
                         [Cue(0, 10, "X", 1, 1), Cue(20, 30, "X", 1, 3)])

    def test_tolerance_and_insert(self):
        a, b = Cue(1, 5, "wrap\nline", 1), Cue(2, 6, "wrap line", 2)
        self.assertEqual(audit([a], [b], 1), [])
        self.assertEqual(audit([a], [b], 0)[0]["start_drift_ms"], 1)
        self.assertEqual(audit([a], [Cue(0, 1, "extra", 1), b], 1)[0]["kind"], "insert")

    def test_cli_example(self):
        root = Path(__file__).resolve().parent
        cmd = [sys.executable, str(root / "cutline_audit.py"), "examples/source.srt",
               "examples/keep.csv", "examples/export.srt"]
        import json
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["differences"][0]["start_drift_ms"], 250)
        self.assertEqual(subprocess.run(cmd + ["--tolerance-ms","250"], cwd=root,
                                        capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(cmd + ["--tolerance-ms","-1"], cwd=root,
                                        capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
