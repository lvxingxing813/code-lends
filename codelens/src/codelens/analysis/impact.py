import re
from typing import Iterable, List, Set

from codelens.agents.review_agent import review_requirement
from codelens.analysis.regression import build_regression_item
from codelens.analysis.risk import score_node
from codelens.graph.models import Graph, Node
from codelens.graph.query import degree_by_node, reachable_nodes

ALIASES = {
    "登录": ["login", "auth", "session"],
    "验证码": ["login", "verify", "captcha", "code"],
    "用户": ["user", "profile", "account"],
    "订单": ["order", "checkout"],
    "下单": ["order", "checkout"],
    "支付": ["pay", "payment", "checkout"],
    "批量": ["batch", "import", "upload"],
    "导入": ["import", "upload"],
    "上传": ["upload", "file"],
    "权限": ["permission", "auth", "role"],
}


def analyze_impact(requirement: str, graph: Graph) -> dict:
    node_by_id = {node.id: node for node in graph.nodes}
    direct_nodes = _match_direct_nodes(requirement, graph.nodes)
    direct_ids = [node.id for node in direct_nodes]
    indirect_ids = [node_id for node_id in reachable_nodes(graph, direct_ids, max_depth=3) if node_id not in direct_ids]
    degree = degree_by_node(graph)
    feature_points = [node.id for node in graph.nodes if node.type in {"Page", "Component", "API", "Feature"}]
    logic_issues = review_requirement(requirement)

    risk_map = {}
    for node_id in direct_ids + indirect_ids:
        node = node_by_id.get(node_id)
        if node is None:
            continue
        score, reason = score_node(node, direct=node_id in direct_ids, degree=degree.get(node_id, 0))
        risk_map[node_id] = {"score": score, "reason": reason}

    regression_list = []
    for node_id in direct_ids + indirect_ids:
        node = node_by_id.get(node_id)
        if node is None or node.type not in {"Feature", "Page", "API", "Module", "Component"}:
            continue
        regression_list.append(build_regression_item(node, direct=node_id in direct_ids))

    return {
        "requirement": requirement,
        "featurePoints": feature_points,
        "matchedFeatures": direct_ids,
        "relatedFeatures": indirect_ids,
        "logicIssues": logic_issues,
        "regressionPoints": regression_list,
        "directImpact": direct_ids,
        "indirectImpact": indirect_ids,
        "riskMap": risk_map,
        "regressionList": regression_list,
        "issues": logic_issues,
        "warnings": [],
    }


def _match_direct_nodes(requirement: str, nodes: Iterable[Node]) -> List[Node]:
    requirement_tokens = _requirement_tokens(requirement)
    matches = []
    seen: Set[str] = set()

    for node in nodes:
        node_text = " ".join(_node_tokens(node)).lower()
        if any(token in node_text for token in requirement_tokens):
            if node.id not in seen:
                seen.add(node.id)
                matches.append(node)

    return matches


def _requirement_tokens(requirement: str) -> Set[str]:
    lowered = requirement.lower()
    tokens: Set[str] = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{1,}", lowered))

    for chinese, aliases in ALIASES.items():
        if chinese in requirement:
            tokens.update(alias.lower() for alias in aliases)
            tokens.add(chinese)
        if chinese == "导入" and chinese in requirement:
            tokens.update({"batch", "import", "upload"})
        if chinese == "上传" and chinese in requirement:
            tokens.update({"upload", "file"})

    for word in re.findall(r"[\u4e00-\u9fff]{2,}", requirement):
        tokens.add(word)

    return {token for token in tokens if len(token) >= 2}


def _node_tokens(node: Node) -> List[str]:
    tokens = [node.id, node.type, node.name]
    if node.path:
        tokens.append(node.path)
    for value in node.metadata.values():
        if isinstance(value, (str, int, float)):
            tokens.append(str(value))
        elif isinstance(value, list):
            tokens.extend(str(item) for item in value)
    return tokens
