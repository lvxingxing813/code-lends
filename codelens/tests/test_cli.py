import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from codelens.cli import main


class CliTest(unittest.TestCase):
    def test_cli_version(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["version"])

        self.assertEqual(code, 0)
        self.assertIn("0.1.0", stdout.getvalue())

    def test_scan_and_analyze_generate_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app_file = root / "app.py"
            app_file.write_text(
                """
from fastapi import APIRouter
router = APIRouter()
@router.post("/api/login")
def login():
    return {"ok": True}
""".strip(),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                scan_code = main(["scan", str(root)])
                analyze_code = main(["analyze", "修改用户登录验证码规则", "--project", str(root)])

            self.assertEqual(scan_code, 0)
            self.assertEqual(analyze_code, 0)
            self.assertTrue((root / ".codelens" / "graph.json").exists())
            self.assertTrue((root / ".codelens" / "report.json").exists())

    def test_export_generates_static_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app_file = root / "app.py"
            app_file.write_text(
                """
from fastapi import APIRouter
router = APIRouter()
@router.post("/api/login")
def login():
    return {"ok": True}
""".strip(),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["scan", str(root)]), 0)
                self.assertEqual(main(["analyze", "修改用户登录验证码规则", "--project", str(root)]), 0)
                code = main(["export", "--project", str(root)])

            html = (root / ".codelens" / "report.html").read_text(encoding="utf-8")
            self.assertEqual(code, 0)
            self.assertIn("CodeLens Demo Report", html)
            self.assertIn("graph-data", html)
            self.assertIn("修改用户登录验证码规则", html)

    def test_analyze_missing_graph_returns_error(self):
        with tempfile.TemporaryDirectory() as directory:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["analyze", "修改登录", "--project", directory])

            self.assertEqual(code, 2)
            self.assertIn("Graph not found", stderr.getvalue())

    def test_analyze_damaged_graph_returns_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph_file = root / ".codelens" / "graph.json"
            graph_file.parent.mkdir()
            graph_file.write_text("{not-json", encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["analyze", "修改登录", "--project", directory])

            self.assertEqual(code, 2)
            self.assertIn("Graph file is damaged", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
