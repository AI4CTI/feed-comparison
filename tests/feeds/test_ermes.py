import builtins
import sys

import pytest

from feed_comparison.feeds.ermes import Ermes, _iocs_to_rows, _parse_iso8601
from feed_comparison.settings import (
    MissingCredentialsError,
    MissingOptionalDependencyError,
    Settings,
)


def test_parse_iso8601_handles_zulu_suffix():
    dt = _parse_iso8601("2026-04-29T12:34:56Z")
    assert dt.year == 2026
    assert dt.tzinfo is not None  # offset-aware


def test_parse_iso8601_handles_explicit_offset():
    dt = _parse_iso8601("2026-04-29T12:34:56+02:00")
    assert dt.utcoffset().total_seconds() == 2 * 3600


def test_iocs_to_rows_maps_full_payload():
    rows = _iocs_to_rows(
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
    assert len(rows) == 1
    row = rows[0]
    assert row["url"] == "http://evil.example.com/login"
    assert row["confidence"] == 0.92
    assert row["threat_type"] == "phishing"  # first element
    assert row["target"] == "Acme Bank"


def test_iocs_to_rows_drops_entries_without_url_or_discovered():
    rows = _iocs_to_rows(
        [
            {"url": "", "discovered": "2026-04-29T12:00:00Z"},
            {"url": "http://x.example.com/", "discovered": ""},
            {"url": "http://valid.example.com/", "discovered": "2026-04-29T12:00:00Z"},
        ]
    )
    assert len(rows) == 1
    assert rows[0]["url"] == "http://valid.example.com/"


def test_iocs_to_rows_tolerates_missing_optional_fields():
    rows = _iocs_to_rows(
        [{"url": "http://minimal.example.com/", "discovered": "2026-04-29T12:00:00Z"}]
    )
    assert len(rows) == 1
    assert rows[0]["confidence"] is None
    assert rows[0]["threat_type"] is None
    assert rows[0]["target"] is None


def test_iocs_to_rows_with_empty_iter_returns_empty_list():
    assert _iocs_to_rows(iter([])) == []


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
