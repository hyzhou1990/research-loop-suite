def dedup_findings(candidates, seen_keys):
    seen = set(seen_keys)
    return [f for f in candidates if f["dedup_key"] not in seen]
