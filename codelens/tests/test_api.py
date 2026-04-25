import json
import tempfile
import unittest
from pathlib import Path

from codelens.api.server import create_handler
from codelens.api.server import _dashboard_html
from codelens.graph.models import Graph, Node
from codelens.graph.store import save_graph


class ApiTest(unittest.TestCase):
    def test_create_handler_has_project_bound_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_graph(
                Graph(root=str(root), nodes=[Node(id="feature:login", type="Feature", name="用户登录")]),
                root / ".codelens" / "graph.json",
            )

            handler = create_handler(root)

            self.assertTrue(hasattr(handler, "do_GET"))

    def test_graph_json_is_readable_for_api_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / ".codelens" / "graph.json"
            save_graph(
                Graph(root=str(root), nodes=[Node(id="feature:login", type="Feature", name="用户登录")]),
                output,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(payload["nodes"][0]["name"], "用户登录")

    def test_dashboard_html_contains_impact_graph(self):
        html = _dashboard_html()

        self.assertIn("影响链路图", html)
        self.assertIn('id="stage"', html)
        self.assertIn("/api/graph", html)


if __name__ == "__main__":
    unittest.main()
