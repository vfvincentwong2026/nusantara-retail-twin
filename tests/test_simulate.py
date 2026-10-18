"""simulate 命令测试：模拟档案产物完整性。"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from nrt.cli.main import app


class TestSimulateCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = Path(tempfile.mkdtemp(prefix="nrt-sim-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_simulate_outputs_archive(self):
        result = self.runner.invoke(
            app,
            [
                "simulate",
                "--store-size", "500",
                "--region", "java",
                "--start-date", "2026-01-10",
                "--days", "30",
                "--include-ramadan",
                "--sku-limit", "30",
                "--output", str(self.tmp),
            ],
        )
        self.assertEqual(result.exit_code, 0, result.output)

        sim_dirs = list(self.tmp.glob("sim-*"))
        self.assertEqual(len(sim_dirs), 1)
        out = sim_dirs[0]
        for name in ("meta.json", "seed.json", "forecast.json", "replenishment.json", "planogram.json", "summary.md"):
            self.assertTrue((out / name).exists(), f"缺少产物 {name}")

        meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["store_size_sqm"], 500)
        self.assertTrue(meta["include_ramadan"])

        forecast = json.loads((out / "forecast.json").read_text(encoding="utf-8"))
        self.assertEqual(len(forecast), 30)
        self.assertIn("daily_forecast", forecast[0]["horizon"])

        rep = json.loads((out / "replenishment.json").read_text(encoding="utf-8"))
        self.assertIn("summary", rep)
        self.assertEqual(rep["summary"]["checked"], 30)

        planogram = json.loads((out / "planogram.json").read_text(encoding="utf-8"))
        total = sum(a["allocated_facings"] for a in planogram["allocations"])
        self.assertEqual(total, planogram["total_facings"])

        summary = (out / "summary.md").read_text(encoding="utf-8")
        self.assertIn("补货汇总", summary)
        self.assertIn("空间优化", summary)


if __name__ == "__main__":
    unittest.main()
