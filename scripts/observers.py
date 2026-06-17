import hashlib
from pathlib import Path

from scripts import openalex

REGISTRY = {}


def register(watcher_id):
    def deco(fn):
        REGISTRY[watcher_id] = fn
        return fn
    return deco


def get_observer(watcher_id):
    return REGISTRY[watcher_id]


@register("lit")
def lit_observer(spec):
    inputs = (spec.get("observe") or {}).get("inputs") or {}
    query = inputs.get("query")
    if not query:
        raise ValueError("lit observer requires inputs.query")
    url = openalex.build_url(
        query,
        from_date=inputs.get("from_date"),
        mailto=inputs.get("mailto"),
        per_page=inputs.get("per_page", 50),
    )
    payload = openalex.fetch_works(url)
    return openalex.parse_works(payload, query)


@register("field")
def field_observer(spec):
    # Wired to preprint feeds in Phase 3b. Returns [] until then.
    return []


@register("manuscript")
def manuscript_observer(spec):
    # Wired to claim-integrity checks in Phase 3b. Returns [] until then.
    return []


@register("data")
def data_observer(spec):
    """Local + deterministic: flag artifacts whose content hash changed vs recorded baseline."""
    from scripts.findings import make_finding
    inputs = spec.get("observe", {}).get("inputs", [])
    findings = []
    for entry in inputs:
        p = Path(entry)
        if not p.exists():
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        findings.append(make_finding(
            dedup_key=f"{p.name}:{digest}",
            type="artifact_change",
            severity="medium",
            item=str(p),
            why_it_matters="artifact content hash differs from previously seen state",
            suggested_action="review whether results changed; re-run reproducibility check",
        ))
    return findings
