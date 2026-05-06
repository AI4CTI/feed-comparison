from datetime import datetime, timedelta

import responses
from typer.testing import CliRunner

from feed_comparison.cli.app import app
from feed_comparison.feeds.phishstats import _API_URL

runner = CliRunner()


@responses.activate
def test_download_writes_csv(tmp_path, monkeypatch):
    monkeypatch.setattr("feed_comparison.feeds.phishstats._REQUEST_DELAY_S", 0)
    now = datetime.utcnow()
    responses.add(
        responses.GET,
        f"{_API_URL}&_p=0",
        json=[
            {
                "url": "http://x.example.com/",
                "date": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        ],
        status=200,
    )
    # Page 1 empty stops the loop.
    responses.add(responses.GET, f"{_API_URL}&_p=1", json=[], status=200)

    result = runner.invoke(
        app, ["download", "phishstats", "--days", "1", "--output-dir", str(tmp_path)]
    )
    assert result.exit_code == 0, result.stdout
    csvs = list(tmp_path.glob("dataframe_phishstats_*.csv"))
    assert len(csvs) == 1
    assert csvs[0].stat().st_size > 0


def test_download_unknown_feed_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["download", "no-such-feed", "--output-dir", str(tmp_path)])
    assert result.exit_code != 0


@responses.activate
def test_download_continues_when_one_feed_lacks_credentials(tmp_path, monkeypatch):
    """A feed that errors out (e.g. missing credentials) should not abort the
    whole `download` command — the other requested feeds must still be tried."""
    monkeypatch.setattr("feed_comparison.feeds.phishstats._REQUEST_DELAY_S", 0)
    monkeypatch.delenv("PHISHTANK_USERNAME", raising=False)
    now = datetime.utcnow()
    responses.add(
        responses.GET,
        f"{_API_URL}&_p=0",
        json=[
            {
                "url": "http://x.example.com/",
                "date": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        ],
        status=200,
    )
    responses.add(responses.GET, f"{_API_URL}&_p=1", json=[], status=200)

    result = runner.invoke(
        app,
        ["download", "phishtank", "phishstats", "--days", "1", "--output-dir", str(tmp_path)],
    )
    # phishtank fails (no credentials) but phishstats succeeds: exit 0, one CSV.
    assert result.exit_code == 0, result.stdout
    csvs = list(tmp_path.glob("dataframe_*.csv"))
    assert len(csvs) == 1
    assert csvs[0].name.startswith("dataframe_phishstats_")


def test_download_exits_nonzero_when_all_feeds_fail(tmp_path, monkeypatch):
    monkeypatch.delenv("PHISHTANK_USERNAME", raising=False)
    monkeypatch.delenv("URLSCAN_TOKEN", raising=False)
    result = runner.invoke(app, ["download", "phishtank", "urlscan", "--output-dir", str(tmp_path)])
    assert result.exit_code == 2
