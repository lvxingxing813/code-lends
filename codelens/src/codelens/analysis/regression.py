from codelens.graph.models import Node


def build_regression_item(node: Node, direct: bool) -> dict:
    priority = "P0" if direct else "P1"
    reason = "直接改动或需求命中" if direct else "依赖链路间接受影响"
    return {
        "feature": node.name,
        "priority": priority,
        "reason": reason,
        "nodeId": node.id,
    }

