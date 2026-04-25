def review_requirement(requirement: str) -> list:
    issues = []
    lowered = requirement.lower()

    if _looks_like_upload_or_import(requirement, lowered) and not _mentions_limits(requirement):
        issues.append(
            {
                "type": "边界缺失",
                "description": "批量导入或上传需求未说明单次上限、文件大小、失败处理策略",
                "severity": "medium",
                "suggestion": "补充文件大小、行数上限、格式校验、失败回滚和部分成功处理规则",
            }
        )

    if "未登录" in requirement and "下单" in requirement:
        issues.append(
            {
                "type": "逻辑矛盾",
                "description": "需求允许未登录下单，可能与现有下单登录态校验冲突",
                "severity": "high",
                "suggestion": "明确是否修改登录校验、游客身份、支付后绑定和风控规则",
            }
        )

    if ("权限" in requirement or "角色" in requirement) and "管理员" not in requirement and "范围" not in requirement:
        issues.append(
            {
                "type": "边界缺失",
                "description": "权限相关需求未说明角色范围和越权处理",
                "severity": "medium",
                "suggestion": "补充角色矩阵、接口鉴权、前端入口控制和审计日志规则",
            }
        )

    return issues


def _looks_like_upload_or_import(requirement: str, lowered: str) -> bool:
    return any(keyword in requirement for keyword in ["批量", "导入", "上传"]) or "upload" in lowered


def _mentions_limits(requirement: str) -> bool:
    keywords = ["上限", "大小", "限制", "行数", "mb", "MB", "回滚", "失败", "格式"]
    return any(keyword in requirement for keyword in keywords)

