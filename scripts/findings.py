VALID_SEVERITY = {"low", "medium", "high", "critical"}


def make_finding(dedup_key, type, severity, item, why_it_matters, suggested_action):
    if not dedup_key:
        raise ValueError("dedup_key must be non-empty")
    if severity not in VALID_SEVERITY:
        raise ValueError(f"invalid severity: {severity}")
    return {
        "dedup_key": dedup_key,
        "type": type,
        "severity": severity,
        "item": item,
        "why_it_matters": why_it_matters,
        "suggested_action": suggested_action,
        "status": "new",
    }
