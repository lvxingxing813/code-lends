from codelens.graph.models import Node


def score_node(node: Node, direct: bool, degree: int = 0) -> tuple:
    complexity = float(node.metadata.get("complexity", 1) or 1)
    change_freq = float(node.metadata.get("changeFreq", 0) or 0)
    bug_history = float(node.metadata.get("bugHistory", 0) or 0)
    base = 0.48 if direct else 0.28
    type_bonus = {
        "API": 0.08,
        "DataModel": 0.1,
        "Module": 0.06,
        "Page": 0.05,
        "Feature": 0.04,
    }.get(node.type, 0.02)
    score = min(1.0, base + type_bonus + complexity * 0.05 + change_freq * 0.03 + bug_history * 0.08 + degree * 0.015)

    reasons = []
    if direct:
        reasons.append("需求关键词直接命中")
    else:
        reasons.append("依赖链路间接受影响")
    if bug_history:
        reasons.append("历史 bug 次数 %d" % int(bug_history))
    if complexity > 1:
        reasons.append("复杂度 %d" % int(complexity))
    if degree >= 3:
        reasons.append("关联节点 %d 个" % degree)

    return round(score, 2), "，".join(reasons)

