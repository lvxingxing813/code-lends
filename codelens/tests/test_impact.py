import unittest

from codelens.analysis.impact import analyze_impact
from codelens.graph.models import Edge, Graph, Node
from codelens.graph.query import neighbors, reachable_nodes


class ImpactTest(unittest.TestCase):
    def test_reachable_nodes_follows_dependency_edges(self):
        graph = Graph(
            root="/tmp/project",
            nodes=[
                Node(id="feature:login", type="Feature", name="登录"),
                Node(id="api:POST /api/login", type="API", name="POST /api/login"),
                Node(id="module:auth", type="Module", name="auth"),
            ],
            edges=[
                Edge(source="feature:login", target="api:POST /api/login", type="CALLS"),
                Edge(source="api:POST /api/login", target="module:auth", type="CALLS"),
            ],
        )

        self.assertEqual(neighbors(graph, "feature:login"), ["api:POST /api/login"])
        self.assertEqual(
            reachable_nodes(graph, ["feature:login"], max_depth=2, include_reverse=False),
            ["api:POST /api/login", "module:auth"],
        )

    def test_analyze_impact_matches_requirement_keywords(self):
        graph = Graph(
            root="/tmp/project",
            nodes=[
                Node(id="feature:login", type="Feature", name="用户登录"),
                Node(id="api:POST /api/login", type="API", name="POST /api/login"),
                Node(id="module:auth", type="Module", name="auth", metadata={"bugHistory": 3}),
            ],
            edges=[
                Edge(source="feature:login", target="api:POST /api/login", type="CALLS"),
                Edge(source="api:POST /api/login", target="module:auth", type="CALLS"),
            ],
        )

        report = analyze_impact("修改用户登录验证码规则", graph)

        self.assertIn("feature:login", report["directImpact"])
        self.assertIn("api:POST /api/login", report["directImpact"])
        self.assertIn("module:auth", report["directImpact"])
        self.assertGreater(report["riskMap"]["module:auth"]["score"], 0.5)
        self.assertEqual(report["regressionList"][0]["priority"], "P0")

    def test_analyze_impact_flags_batch_upload_missing_limits(self):
        report = analyze_impact("新增用户批量导入功能，支持 Excel 上传", Graph(root="/tmp/project"))

        self.assertEqual(report["issues"][0]["type"], "边界缺失")
        self.assertIn("文件大小", report["issues"][0]["suggestion"])


if __name__ == "__main__":
    unittest.main()

