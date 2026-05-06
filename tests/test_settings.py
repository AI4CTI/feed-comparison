from pathlib import Path

import pytest

from feed_comparison.settings import (
    MissingCredentialsError,
    MissingOptionalDependencyError,
    Settings,
)


def test_settings_from_env_defaults_when_unset(monkeypatch):
    for var in (
        "MISP_URL",
        "MISP_KEY",
        "PHISHTANK_USERNAME",
        "URLSCAN_URL",
        "URLSCAN_TOKEN",
        "FEED_COMPARISON_OUTPUT_DIR",
    ):
        monkeypatch.delenv(var, raising=False)
    settings = Settings.from_env(env_file=Path("/nonexistent"))
    assert settings.misp_url is None
    assert settings.phishtank_username is None
    assert settings.output_dir == Path("./output")


def test_settings_from_env_picks_up_values(monkeypatch):
    monkeypatch.setenv("PHISHTANK_USERNAME", "stefano")
    monkeypatch.setenv("FEED_COMPARISON_OUTPUT_DIR", "/tmp/fc-out")
    settings = Settings.from_env(env_file=Path("/nonexistent"))
    assert settings.phishtank_username == "stefano"
    assert settings.output_dir == Path("/tmp/fc-out")


def test_settings_require_returns_values():
    s = Settings(phishtank_username="alice")
    (got,) = s.require("phishtank_username")
    assert got == "alice"


def test_settings_require_raises_when_missing():
    s = Settings()
    with pytest.raises(MissingCredentialsError) as exc:
        s.require("phishtank_username", "urlscan_token")
    assert "phishtank_username" in exc.value.missing
    assert "urlscan_token" in exc.value.missing
    assert "PHISHTANK_USERNAME" in str(exc.value)


def test_missing_optional_dependency_error_message_is_actionable():
    err = MissingOptionalDependencyError("misp", ["pymisp"])
    assert err.extra == "misp"
    assert "pymisp" in err.packages
    msg = str(err)
    assert "feed-comparison[misp]" in msg
    assert "pymisp" in msg
