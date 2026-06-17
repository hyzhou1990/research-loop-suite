_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_interval(s):
    """'30m'/'6h'/'1d'/'2w'/'45s' -> seconds; unknown/empty -> None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    unit = s[-1:]
    if unit not in _UNIT_SECONDS:
        return None
    try:
        value = int(s[:-1])
    except ValueError:
        return None
    return value * _UNIT_SECONDS[unit]


def classify(last_run, now, blocked):
    """Return (health, age_seconds). Precedence: blocked > error > stale > ok."""
    age = now - last_run["ts"]
    if blocked:
        return "blocked", age
    if last_run.get("decision") == "error":
        return "error", age
    cadence = last_run.get("cadence") or {}
    if cadence.get("mode") in ("cron", "self-paced"):
        interval = parse_interval(cadence.get("every"))
        if interval is not None and age > 2 * interval:
            return "stale", age
    return "ok", age
