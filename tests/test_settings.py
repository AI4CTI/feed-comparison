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
        "ERMES_API_SERVER",
        "ERMES_CLIENT_ID",
        "ERMES_CLIENT_SECRET",
        "FEED_COMPARISON_OUTPUT_DIR",
    ):
        monkeypatch.delenv(var, raising=False)
    settings = Settings.from_env(env_file=Path("/nonexistent"))
    assert settings.misp_url is None
    assert settings.phishtank_username is None
    assert settings.ermes_api_server is None
    assert settings.ermes_client_id is None
    assert settings.ermes_client_secret is None
    assert settings.output_dir == Path("./output")


def test_settings_from_env_picks_up_values(monkeypatch):
    monkeypatch.setenv("PHISHTANK_USERNAME", "stefano")
    monkeypatch.setenv("FEED_COMPARISON_OUTPUT_DIR", "/tmp/fc-out")
    settings = Settings.from_env(env_file=Path("/nonexistent"))
    assert settings.phishtank_username == "stefano"
    assert settings.output_dir == Path("/tmp/fc-out")


def test_settings_from_env_picks_up_ermes_credentials(monkeypatch):
    monkeypatch.setenv("ERMES_API_SERVER", "https://api.example.ermes.company")
    monkeypatch.setenv("ERMES_CLIENT_ID", "id-123")
    monkeypatch.setenv("ERMES_CLIENT_SECRET", "secret-xyz")
    settings = Settings.from_env(env_file=Path("/nonexistent"))
    assert settings.ermes_api_server == "https://api.example.ermes.company"
    assert settings.ermes_client_id == "id-123"
    assert settings.ermes_client_secret == "secret-xyz"


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


def test_settings_repr_masks_secret_fields():
    s = Settings(
        misp_url="https://misp.example.org",
        misp_key="super-secret-misp",
        phishtank_username="alice",
        urlscan_url="https://urlscan.io/api/v1/search/",
        urlscan_token="super-secret-urlscan",
        ermes_api_server="https://api.example.ermes.company",
        ermes_client_id="oauth-client-id-XYZ",
        ermes_client_secret="oauth-secret-XYZ",
    )
    rendered = repr(s)
    # Non-secret fields stay readable (debugging is the point of __repr__).
    assert "https://misp.example.org" in rendered
    assert "alice" in rendered
    assert "https://urlscan.io/api/v1/search/" in rendered
    assert "https://api.example.ermes.company" in rendered
    # Secret fields are masked, regardless of how they are formatted.
    assert "super-secret-misp" not in rendered
    assert "super-secret-urlscan" not in rendered
    assert "oauth-client-id-XYZ" not in rendered
    assert "oauth-secret-XYZ" not in rendered
    assert "'***'" in rendered


def test_settings_repr_does_not_mask_unset_secrets():
    s = Settings()
    rendered = repr(s)
    # An unset secret stays as `None`, not `'***'`.
    assert "misp_key=None" in rendered
    assert "ermes_client_secret=None" in rendered
