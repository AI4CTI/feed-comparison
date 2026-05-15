import builtins
import sys

import pytest

from feed_comparison.feeds.ermes import Ermes, _iocs_to_rows, _parse_iso8601
from feed_comparison.settings import (
    FeedConfigurationError,
    MissingCredentialsError,
    MissingOptionalDependencyError,
    Settings,
)


def test_parse_iso8601_handles_zulu_suffix():
    dt = _parse_iso8601("2026-04-29T12:34:56Z")
    assert dt.year == 2026
    # Normalised to tz-naive UTC for compatibility with the other feeds
    assert dt.tzinfo is None


def test_parse_iso8601_handles_explicit_offset():
    # +02:00 means 12:34:56 local == 10:34:56 UTC
    dt = _parse_iso8601("2026-04-29T12:34:56+02:00")
    assert dt.tzinfo is None
    assert dt.hour == 10
    assert dt.minute == 34


def test_iocs_to_rows_maps_full_payload():
    rows, n_skipped = _iocs_to_rows(
        [
            {
                "url": "http://evil.example.com/login",
                "discovered": "2026-04-29T12:00:00Z",
                "threat_types": ["phishing", "phishing_suspicious"],
                "confidence": 0.92,
                "target": "Acme Bank",
            }
        ]
    )
    assert n_skipped == 0
    assert len(rows) == 1
    row = rows[0]
    assert row["url"] == "http://evil.example.com/login"
    assert row["confidence"] == 0.92
    assert row["threat_type"] == "phishing"  # first element
    assert row["target"] == "Acme Bank"


def test_iocs_to_rows_drops_entries_without_url_or_discovered():
    rows, n_skipped = _iocs_to_rows(
        [
            {"url": "", "discovered": "2026-04-29T12:00:00Z"},
            {"url": "http://x.example.com/", "discovered": ""},
            {"url": "http://valid.example.com/", "discovered": "2026-04-29T12:00:00Z"},
        ]
    )
    assert n_skipped == 0
    assert len(rows) == 1
    assert rows[0]["url"] == "http://valid.example.com/"


def test_iocs_to_rows_tolerates_missing_optional_fields():
    rows, n_skipped = _iocs_to_rows(
        [{"url": "http://minimal.example.com/", "discovered": "2026-04-29T12:00:00Z"}]
    )
    assert n_skipped == 0
    assert len(rows) == 1
    assert rows[0]["confidence"] is None
    assert rows[0]["threat_type"] is None
    assert rows[0]["target"] is None


def test_iocs_to_rows_with_empty_iter_returns_empty_list():
    assert _iocs_to_rows(iter([])) == ([], 0)


def test_iocs_to_rows_skips_entries_with_undocumented_metadata_fields():
    """Defensive schema check: an IoC whose metadata carries a field
    outside the documented public TAXII schema is skipped, and counted
    against `n_skipped` so the caller can surface the count in DEBUG logs."""
    rows, n_skipped = _iocs_to_rows(
        [
            {
                "url": "http://standard.example.com/",
                "discovered": "2026-04-29T12:00:00Z",
                "confidence": 0.5,
            },
            {
                "url": "http://has-extra-field.example.com/",
                "discovered": "2026-04-29T12:00:00Z",
                "confidence": 0.5,
                "some_undocumented_field": "anything",
            },
        ]
    )
    assert len(rows) == 1
    assert rows[0]["url"] == "http://standard.example.com/"
    assert n_skipped == 1


def test_iocs_to_rows_accepts_all_documented_fields_together():
    """Sanity: an IoC populating every documented field at once is kept."""
    rows, n_skipped = _iocs_to_rows(
        [
            {
                "url": "http://full.example.com/",
                "discovered": "2026-04-29T12:00:00Z",
                "confidence": 0.9,
                "threat_types": ["phishing"],
                "ip_addresses": ["1.2.3.4"],
                "screenshot_url": "https://shot.example.com/x.png",
                "langs_detected": {"en": 0.99},
                "target": "Acme",
            }
        ]
    )
    assert n_skipped == 0
    assert len(rows) == 1


def test_ermes_fetch_raises_when_credentials_missing():
    with pytest.raises(MissingCredentialsError) as exc:
        Ermes().fetch(days=1, settings=Settings())
    assert "ermes_api_server" in exc.value.missing
    assert "ermes_client_id" in exc.value.missing
    assert "ermes_client_secret" in exc.value.missing


def test_ermes_fetch_raises_missing_optional_when_libs_unimportable(monkeypatch):
    """Simulate a user that installed feed-comparison without the [ermes] extra."""
    real_import = builtins.__import__
    blocked = {"taxii2client", "taxii2client.v21", "requests_oauth2client"}

    def fake_import(name, *args, **kwargs):
        if name in blocked or any(name.startswith(b + ".") for b in blocked):
            raise ImportError(f"No module named '{name}' (simulated)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    # Drop any cached module so our patched __import__ is exercised.
    for mod in list(sys.modules):
        if mod.startswith("taxii2client") or mod.startswith("requests_oauth2client"):
            monkeypatch.delitem(sys.modules, mod, raising=False)

    settings = Settings(
        ermes_api_server="https://api.example.com",
        ermes_client_id="id",
        ermes_client_secret="secret",
    )
    with pytest.raises(MissingOptionalDependencyError) as exc:
        Ermes().fetch(days=1, settings=settings)
    assert exc.value.extra == "ermes"
    msg = str(exc.value)
    assert "taxii2-client" in msg
    assert "requests-oauth2client" in msg


def test_ermes_fetch_translates_oauth_errors_to_feed_configuration_error(monkeypatch):
    """Server-side rejection of credentials must come out as a typed
    FeedConfigurationError mentioning the env vars to check, not as a raw
    OAuth2 traceback."""
    pytest.importorskip("requests_oauth2client")
    from requests_oauth2client.exceptions import OAuth2Error

    class _FakeOAuth2Error(OAuth2Error):
        # Bypass the parent __init__ (which requires real Response / Client
        # instances we'd have to fabricate just to satisfy attrs validation).
        def __init__(self):
            Exception.__init__(self, "invalid_client (simulated)")

        def __str__(self):
            return "invalid_client: The client does not exist on this server"

    def explode(self, *_args, **_kwargs):
        raise _FakeOAuth2Error()

    monkeypatch.setattr("requests_oauth2client.OAuth2ClientCredentialsAuth.renew_token", explode)

    settings = Settings(
        ermes_api_server="https://api.example.com",
        ermes_client_id="bad-id",
        ermes_client_secret="bad-secret",
    )
    with pytest.raises(FeedConfigurationError) as exc:
        Ermes().fetch(days=1, settings=settings)
    msg = str(exc.value)
    assert "ERMES_API_SERVER" in msg
    assert "ERMES_CLIENT_ID" in msg
    assert "ERMES_CLIENT_SECRET" in msg


def test_ermes_fetch_stops_at_max_pages_safety_with_warning(monkeypatch, caplog):
    """Regression: a misbehaving Ermes server that paginated forever used to
    leave the client looping indefinitely. The safety cap must trip with a
    clear WARNING that explicitly tells the user the download is partial."""
    pytest.importorskip("requests_oauth2client")
    pytest.importorskip("taxii2client")

    monkeypatch.setattr("feed_comparison.feeds.ermes._MAX_PAGES_SAFETY", 3)

    # Skip the real OAuth + ApiRoot setup by short-circuiting the bits of
    # taxii2client that touch the network. We replace `as_pages` with our
    # own infinite generator and stub `ApiRoot` so its `.collections[0]`
    # access doesn't try to talk to a real TAXII server.
    def infinite_pages(*_args, **_kwargs):
        page_index = 0
        while True:
            page_index += 1
            yield {
                "objects": [
                    {
                        "ermes_metadata": {
                            "url": f"http://e{page_index}.example.com/",
                            "discovered": "2026-04-29T12:00:00Z",
                        }
                    }
                ]
            }

    class _FakeCollection:
        def get_objects(self, *_a, **_k):
            return None

    class _FakeApiRoot:
        def __init__(self, *_a, **_k):
            self.collections = [_FakeCollection()]

    monkeypatch.setattr("feed_comparison.feeds.ermes.__name__", "feed_comparison.feeds.ermes")
    monkeypatch.setattr("taxii2client.ApiRoot", _FakeApiRoot)
    monkeypatch.setattr("taxii2client.v21.as_pages", infinite_pages)

    # Also short-circuit OAuth so the test doesn't try to talk to a token
    # endpoint. We just need OAuth2Client/OAuth2ClientCredentialsAuth to be
    # constructible; ApiRoot is faked above so the `auth` is never used.
    settings = Settings(
        ermes_api_server="https://api.example.com",
        ermes_client_id="id",
        ermes_client_secret="secret",
    )
    with caplog.at_level("WARNING", logger="feed_comparison.feeds.ermes"):
        df = Ermes().fetch(days=1, settings=settings)
    assert any("MAX_PAGES_SAFETY=3" in rec.message for rec in caplog.records)
    # Partial result, not a crash, not an infinite loop.
    assert not df.empty


def test_ermes_fetch_early_stops_when_skip_recent_days_passed(monkeypatch, caplog):
    """When the caller asks to skip the last N days, the TAXII pagination
    must short-circuit as soon as the newest IoC seen crosses the upper
    cutoff — saving bandwidth on the most expensive feed. Correctness is
    handled by the caller's post-fetch filter; this is purely an optimisation."""
    pytest.importorskip("requests_oauth2client")
    pytest.importorskip("taxii2client")

    from datetime import datetime, timedelta, timezone

    # 10 pages spaced 1 day apart, ascending (oldest first), the way the
    # real TAXII server returns them. With skip_recent_days=5, pagination
    # should break around page 5-6 — i.e. AS SOON AS newest_seen crosses
    # (now - 5d), so the last few pages are never fetched.
    now = datetime.now(tz=timezone.utc)
    page_dates = [now - timedelta(days=d) for d in (10, 9, 8, 7, 6, 5, 4, 3, 2, 1)]

    pages_yielded = {"count": 0}

    def finite_pages(*_args, **_kwargs):
        for i, d in enumerate(page_dates, start=1):
            pages_yielded["count"] = i
            yield {
                "objects": [
                    {
                        "ermes_metadata": {
                            "url": f"http://page{i}.example.com/",
                            "discovered": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                    }
                ]
            }

    class _FakeCollection:
        def get_objects(self, *_a, **_k):
            return None

    class _FakeApiRoot:
        def __init__(self, *_a, **_k):
            self.collections = [_FakeCollection()]

    monkeypatch.setattr("taxii2client.ApiRoot", _FakeApiRoot)
    monkeypatch.setattr("taxii2client.v21.as_pages", finite_pages)

    settings = Settings(
        ermes_api_server="https://api.example.com",
        ermes_client_id="id",
        ermes_client_secret="secret",
    )
    with caplog.at_level("INFO", logger="feed_comparison.feeds.ermes"):
        df = Ermes().fetch(days=30, settings=settings, skip_recent_days=5)

    # Pagination must stop AS SOON AS newest_seen crosses (now - 5d).
    # That happens around page 6 (date now-5d) or page 7 (date now-4d),
    # depending on clock skew between test setup and check. Either way
    # we must have skipped the tail (pages 8-10 = days now-3d, now-2d, now-1d).
    assert pages_yielded["count"] < 10, (
        f"Expected early-stop before page 10, but consumed all {pages_yielded['count']}"
    )
    assert not df.empty
    assert any("reached upper cutoff" in rec.message for rec in caplog.records)


def test_ermes_fetch_does_not_early_stop_when_skip_recent_days_zero(monkeypatch):
    """Sanity check: with skip_recent_days=0 (the default), pagination
    must consume every page returned by the server."""
    pytest.importorskip("requests_oauth2client")
    pytest.importorskip("taxii2client")

    from datetime import datetime, timedelta, timezone

    now = datetime.now(tz=timezone.utc)
    page_dates = [now - timedelta(days=d) for d in (10, 8, 6, 4, 2, 0)]
    pages_yielded = {"count": 0}

    def finite_pages(*_args, **_kwargs):
        for i, d in enumerate(page_dates, start=1):
            pages_yielded["count"] = i
            yield {
                "objects": [
                    {
                        "ermes_metadata": {
                            "url": f"http://page{i}.example.com/",
                            "discovered": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                    }
                ]
            }

    class _FakeCollection:
        def get_objects(self, *_a, **_k):
            return None

    class _FakeApiRoot:
        def __init__(self, *_a, **_k):
            self.collections = [_FakeCollection()]

    monkeypatch.setattr("taxii2client.ApiRoot", _FakeApiRoot)
    monkeypatch.setattr("taxii2client.v21.as_pages", finite_pages)

    settings = Settings(
        ermes_api_server="https://api.example.com",
        ermes_client_id="id",
        ermes_client_secret="secret",
    )
    df = Ermes().fetch(days=30, settings=settings)
    # All 6 pages consumed; no early-stop because skip_recent_days defaults to 0.
    assert pages_yielded["count"] == 6
    assert len(df) == 6
