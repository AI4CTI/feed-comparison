import json

from typer.testing import CliRunner

from feed_comparison.cli.app import app

runner = CliRunner()


def test_list_feeds_renders_table_with_all_builtin_feeds():
    result = runner.invoke(app, ["list-feeds"])
    assert result.exit_code == 0
    for name in ("misp", "phishstats", "phishtank", "urlscan"):
        assert name in result.stdout


def test_list_feeds_with_credentials_filters_out_anonymous_feeds():
    result = runner.invoke(app, ["list-feeds", "--with-credentials"])
    assert result.exit_code == 0
    assert "phishstats" not in result.stdout  # PhishStats has no required credentials
    assert "phishtank" in result.stdout


def test_list_feeds_json_returns_valid_json():
    result = runner.invoke(app, ["list-feeds", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    by_name = {entry["name"]: entry for entry in payload}
    assert by_name["phishstats"]["requires_credentials"] == []
    assert by_name["urlscan"]["requires_credentials"] == ["urlscan_url", "urlscan_token"]
