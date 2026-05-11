import re
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


@responses.activate
def test_phishstats_stops_at_max_pages_safety_with_warning(monkeypatch, caplog):
    """Regression: a server that keeps returning future-dated entries (so
    `oldest_in_page < cutoff` never triggers) used to loop forever. The
    safety cap must trip with a clear WARNING and stop, returning a
    partial DataFrame instead of looping until the user kills the process."""
    monkeypatch.setattr("feed_comparison.feeds.phishstats._REQUEST_DELAY_S", 0)
    monkeypatch.setattr("feed_comparison.feeds.phishstats._MAX_PAGES_SAFETY", 3)

    now = datetime.utcnow()
    recent = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Every page is non-empty AND newer than the cutoff, so the natural
    # loop exit conditions never fire. Only the safety cap saves us.
    payload = [{"url": f"http://x{i}.example.com/", "date": recent} for i in range(3)]
    responses.add(
        responses.GET,
        re.compile(rf"{re.escape(_API_URL)}&_p=\d+"),
        json=payload,
        status=200,
    )

    with caplog.at_level("WARNING", logger="feed_comparison.feeds.phishstats"):
        df = PhishStats().fetch(days=1, settings=Settings())
    assert any("MAX_PAGES_SAFETY=3" in rec.message for rec in caplog.records)
    # A non-empty (partial) result is returned, not a crash.
    assert not df.empty
