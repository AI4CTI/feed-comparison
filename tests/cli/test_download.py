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
