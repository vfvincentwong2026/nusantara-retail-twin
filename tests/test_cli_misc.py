"""nrt doctor / nrt export 命令测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from nrt.cli.main import app
from nrt.seed import SeedGenerator

runner = CliRunner()


class TestDoctor(unittest.TestCase):
    def test_doctor_passes(self):
        result = runner.invoke(app, ["doctor"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("python", result.output)

    def test_doctor_json(self):
        result = runner.invoke(app, ["doctor", "--format", "json"])
        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertTrue(data["ok"])
        names = {c["name"] for c in data["checks"]}
        self.assertIn("dep:typer", names)


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.seed_file = Path(cls.tmp.name) / "seed.json"
        gen = SeedGenerator(store_size=500, region="java", seed=7)
        cls.seed_file.write_text(
            json.dumps(gen.generate(), ensure_ascii=False), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_export_json_limit(self):
        result = runner.invoke(app, [
            "export", str(self.seed_file), "-s", "skus", "-n", "5", "-f", "json"])
        self.assertEqual(result.exit_code, 0, result.output)
        rows = json.loads(result.output)
        self.assertEqual(len(rows), 5)
        self.assertIn("sku_id", rows[0])

    def test_export_csv(self):
        result = runner.invoke(app, [
            "export", str(self.seed_file), "-s", "zones", "-f", "csv"])
        self.assertEqual(result.exit_code, 0, result.output)
        lines = [l for l in result.output.splitlines() if l.strip()]
        self.assertGreater(len(lines), 1)
        self.assertIn("zone", lines[0].lower())

    def test_export_dict_section(self):
        result = runner.invoke(app, [
            "export", str(self.seed_file), "-s", "store_profile", "-f", "json"])
        self.assertEqual(result.exit_code, 0, result.output)
        profile = json.loads(result.output)
        self.assertIn("store_id", profile)

    def test_export_bad_section(self):
        result = runner.invoke(app, ["export", str(self.seed_file), "-s", "nope"])
        self.assertEqual(result.exit_code, 2)


if __name__ == "__main__":
    unittest.main()


class TestSynthPosBacktest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.seed_file = Path(cls.tmp.name) / "seed.json"
        cls.seed_file.write_text(
            json.dumps(SeedGenerator(store_size=500, region="java", seed=7).generate(),
                       ensure_ascii=False),
            encoding="utf-8")
        cls.pos_file = Path(cls.tmp.name) / "pos.json"
        result = runner.invoke(app, [
            "synth-pos", "-s", str(cls.seed_file), "-d", "120",
            "-o", str(cls.tmp.name)])
        assert result.exit_code == 0, result.output

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_pos_structure(self):
        pos = json.loads(self.pos_file.read_text(encoding="utf-8"))
        self.assertIn("sales", pos)
        self.assertIn("wastage", pos)
        self.assertGreater(pos["summary"]["sale_events"], 0)
        self.assertGreaterEqual(pos["summary"]["censored_days"], 0)

    def test_backtest_runs(self):
        result = runner.invoke(app, [
            "backtest", str(self.pos_file), "-s", str(self.seed_file),
            "--sku-limit", "20"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("MAPE", result.output)

    def test_synth_pos_min_days_guard(self):
        result = runner.invoke(app, [
            "synth-pos", "-s", str(self.seed_file), "-d", "50"])
        self.assertEqual(result.exit_code, 2)


class TestMigrateServe(unittest.TestCase):
    def test_migrate_v02_to_v03(self):
        with tempfile.TemporaryDirectory() as td:
            old = Path(td) / "old.json"
            old.write_text(json.dumps({"meta": {"seed_version": "0.2"}, "skus": []}), encoding="utf-8")
            r = runner.invoke(app, ["migrate", str(old)])
            self.assertEqual(r.exit_code, 0, r.output)
            out = json.loads((Path(td) / "old_migrated.json").read_text(encoding="utf-8"))
            self.assertEqual(out["meta"]["seed_version"], "0.3")
            self.assertIn("sentiment_defaults", out["meta"])

    def test_serve_health_and_seeds(self):
        import threading, urllib.request
        from nrt.cli.commands.serve import _Handler, SEEDS_DIR
        from http.server import ThreadingHTTPServer
        srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        port = srv.server_address[1]
        try:
            health = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/health").read())
            self.assertTrue(health["ok"])
            seeds = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/seeds").read())
            self.assertIsInstance(seeds, list)
        finally:
            srv.shutdown()
