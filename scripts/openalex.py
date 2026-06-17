from urllib.parse import urlencode

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
