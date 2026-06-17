import hashlib
import re
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
def lit_observer(spec, state=None):
    inputs = (spec.get("observe") or {}).get("inputs") or {}
    if not isinstance(inputs, dict):
        raise ValueError("lit observer requires inputs to be a mapping with a 'query' key")
    query = inputs.get("query")
    if not query:
        raise ValueError("lit observer requires inputs.query")
    cursor = (state or {}).get("cursor")
    # cursor "" / None both fall back to the spec from_date (intentional truthiness contract)
    from_date = cursor or inputs.get("from_date")
    try:
        per_page = max(1, min(int(inputs.get("per_page", 50)), 200))  # OpenAlex hard cap
    except (TypeError, ValueError):
        per_page = 50
    url = openalex.build_url(query, from_date=from_date, mailto=inputs.get("mailto"), per_page=per_page)
    payload = openalex.fetch_works(url)
    findings = openalex.parse_works(payload, query)
    dates = [w.get("publication_date") for w in (payload.get("results") or [])
             if isinstance(w, dict)
             and isinstance(w.get("publication_date"), str)
             and re.fullmatch(r"\d{4}-\d{2}-\d{2}", w["publication_date"])]
    candidate_dates = ([cursor] if cursor else []) + dates
    new_cursor = max(candidate_dates) if candidate_dates else None
    return {"findings": findings, "cursor": new_cursor}


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
        try:
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
        except (FileNotFoundError, OSError):
            continue  # input path missing/unreadable this run — skip
        digest = h.hexdigest()[:16]
        findings.append(make_finding(
            dedup_key=f"{p.name}:{digest}",
            type="artifact_change",
            severity="medium",
            item=str(p),
            why_it_matters="artifact content hash differs from previously seen state",
            suggested_action="review whether results changed; re-run reproducibility check",
        ))
    return findings
