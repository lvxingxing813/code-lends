import tempfile
import unittest
from pathlib import Path

from codelens.parsers.python_parser import parse_python_file


class PythonParserTest(unittest.TestCase):
    def test_parse_fastapi_routes_and_functions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "app" / "auth.py"
            source.parent.mkdir()
            source.write_text(
                """
from fastapi import APIRouter
router = APIRouter()

@router.post("/api/login")
def login():
    return {"ok": True}

def check_permission():
    return True
""".strip(),
                encoding="utf-8",
            )

            result = parse_python_file(source, root)
            node_ids = {node.id for node in result.nodes}

            self.assertIn("module:app/auth.py", node_ids)
            self.assertIn("api:POST /api/login", node_ids)
            self.assertIn("function:app/auth.py:login", node_ids)
            self.assertTrue(any(edge.source == "module:app/auth.py" and edge.target == "api:POST /api/login" for edge in result.edges))

    def test_parse_invalid_python_returns_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "broken.py"
            source.write_text("def broken(:", encoding="utf-8")

            result = parse_python_file(source, root)

            self.assertEqual(result.nodes, [])
            self.assertEqual(result.warnings[0].type, "FILE_PARSE_FAILED")


if __name__ == "__main__":
    unittest.main()

