from urllib.parse import urlparse, parse_qs
from scripts.openalex import build_url


def _params(url):
    return parse_qs(urlparse(url).query)


def test_build_url_basic_query():
    url = build_url("RSV prefusion F")
    assert url.startswith("https://api.openalex.org/works?")
    p = _params(url)
    assert p["search"] == ["RSV prefusion F"]
    assert p["sort"] == ["publication_date:desc"]
    assert p["per-page"] == ["50"]
    assert "filter" not in p          # no from_date -> no filter
    assert "mailto" not in p          # no mailto -> omitted


def test_build_url_with_from_date_and_mailto():
    url = build_url("cancer", from_date="2026-01-01", mailto="a@b.com", per_page=10)
    p = _params(url)
    assert p["filter"] == ["from_publication_date:2026-01-01"]
    assert p["mailto"] == ["a@b.com"]
    assert p["per-page"] == ["10"]


def test_build_url_encodes_special_chars():
    url = build_url("p53 & MDM2")
    p = _params(url)
    assert p["search"] == ["p53 & MDM2"]   # round-trips through encoding
