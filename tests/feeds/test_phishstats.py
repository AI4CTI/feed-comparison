from datetime import datetime, timedelta

import responses

from feed_comparison.feeds.phishstats import _API_URL, PhishStats
from feed_comparison.settings import Settings


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@responses.activate
def test_phishstats_fetch_returns_canonical_dataframe(monkeypatch):
    monkeypatch.setattr("feed_comparison.feeds.phishstats._REQUEST_DELAY_S", 0)

    now = datetime.utcnow()
    page0 = [
        {"url": "http://evil-1.example.com/login", "date": _iso(now - timedelta(hours=2))},
        {"url": "http://evil-2.example.com/x", "date": _iso(now - timedelta(hours=5))},
    ]
    # Page 1 returns rows older than the days=1 cutoff so the loop stops.
    page1 = [
        {"url": "http://ancient.example.com/", "date": _iso(now - timedelta(days=30))},
    ]
    responses.add(responses.GET, f"{_API_URL}&_p=0", json=page0, status=200)
    responses.add(responses.GET, f"{_API_URL}&_p=1", json=page1, status=200)

    df = PhishStats().fetch(days=1, settings=Settings())
    assert not df.empty
    assert {"hostname", "domain", "normURLwScheme"}.issubset(df.columns)
    assert any("evil-1.example.com" in h for h in df["hostname"])


@responses.activate
def test_phishstats_returns_empty_on_5xx(monkeypatch):
    monkeypatch.setattr("feed_comparison.feeds.phishstats._REQUEST_DELAY_S", 0)
    responses.add(
        responses.GET,
        f"{_API_URL}&_p=0",
        body="<html>Cloudflare</html>",
        status=522,
    )
    df = PhishStats().fetch(days=1, settings=Settings())
    assert df.empty
