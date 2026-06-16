import hashlib
from pathlib import Path

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
    # Wired to Semantic Scholar / OpenAlex / Crossref in Phase 3b. Returns [] until then.
    return []


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
