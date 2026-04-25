import tempfile
import unittest
from pathlib import Path

from codelens.graph.models import Edge, Graph, Node, WarningItem
from codelens.graph.store import load_graph, save_graph


class GraphStoreTest(unittest.TestCase):
    def test_save_and_load_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph = Graph(
                root=str(root),
                nodes=[Node(id="module:auth", type="Module", name="auth", path="app/auth.py")],
                edges=[Edge(source="module:auth", target="api:POST /api/login", type="EXPOSES")],
                warnings=[
                    WarningItem(
                        type="FILE_PARSE_FAILED",
                        path="broken.py",
                        message="invalid syntax",
                        blocking=False,
                    )
                ],
            )
            output = root / ".codelens" / "graph.json"

            save_graph(graph, output)
            loaded = load_graph(output)

            self.assertEqual(loaded.nodes[0].id, "module:auth")
            self.assertEqual(loaded.edges[0].type, "EXPOSES")
            self.assertFalse(loaded.warnings[0].blocking)


if __name__ == "__main__":
    unittest.main()

