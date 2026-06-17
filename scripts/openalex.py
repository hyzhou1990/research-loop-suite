import json
import time
import urllib.request
from urllib.parse import urlencode

from scripts.findings import make_finding

_BASE = "https://api.openalex.org/works"


def build_url(query, from_date=None, mailto=None, per_page=50):
    params = {
        "search": query,
        "sort": "publication_date:desc",
        "per-page": per_page,
    }
    if from_date:
        params["filter"] = f"from_publication_date:{from_date}"
    if mailto:
        params["mailto"] = mailto
    return f"{_BASE}?{urlencode(params)}"


def parse_works(payload, query):
    results = payload.get("results") or []
    findings = []
    for w in results:
        key = w.get("id") or w.get("doi")
        if not key:
            continue  # cannot dedup without a stable identifier
        title = w.get("title") or "(untitled)"
        year = w.get("publication_year")
        date = w.get("publication_date") or "unknown date"
        cited = w.get("cited_by_count", 0)
        landing = w.get("doi") or w.get("id")
        item = f"{title} ({year})" if year else title
        findings.append(make_finding(
            dedup_key=key,
            type="new_paper",
            severity="medium",
            item=item,
            why_it_matters=f"new paper matching '{query}', published {date}, cited-by {cited}",
            suggested_action=f"read abstract; consider citing — {landing}",
        ))

    count = (payload.get("meta") or {}).get("count")
    if isinstance(count, int) and count > len(results):
        findings.append(make_finding(
            dedup_key=f"coverage:{query}:{count}",
            type="coverage_note",
            severity="low",
            item=f"{count} works matched '{query}'; {len(results)} surfaced this run",
            why_it_matters=f"{count} total matches exceed the per-run cap ({len(results)} returned)",
            suggested_action="narrow the query or raise per_page if you need fuller coverage",
        ))
    return findings


def fetch_works(url, timeout=10, retries=1):
    """Fetch + JSON-decode an OpenAlex URL. Retries once on transient failure,
    then raises RuntimeError. Network layer — keep logic in parse_works."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-loop-suite"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200)
                if status != 200:
                    raise RuntimeError(f"OpenAlex returned HTTP {status}")
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - re-raised as RuntimeError below
            last_err = e
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"OpenAlex fetch failed for {url}: {last_err}")
