from datetime import datetime, timedelta

import responses

from feed_comparison.feeds.phishtank import _DOWNLOAD_URL, PhishTank
from feed_comparison.settings import MissingCredentialsError, Settings


def _csv_payload(rows):
    header = (
        "phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target"
    )
    body_lines = [header]
    for url, ts in rows:
        body_lines.append(f"1,{url},http://phishtank.org/1.html,{ts},yes,{ts},yes,Other")
    return "\n".join(body_lines) + "\n"


@responses.activate
def test_phishtank_filters_by_window_and_canonicalises():
    recent = (datetime.utcnow() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    old = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    responses.add(
        responses.GET,
        _DOWNLOAD_URL,
        body=_csv_payload(
            [("http://recent.example.com/", recent), ("http://old.example.com/", old)]
        ),
        status=200,
        content_type="text/csv",
    )

    df = PhishTank().fetch(days=1, settings=Settings(phishtank_username="anonymous"))
    assert {"hostname", "domain", "normURLwScheme", "discovered_date_pt"}.issubset(df.columns)
    assert len(df) == 1
    assert "recent.example.com" in df["hostname"].iloc[0]


def test_phishtank_raises_when_username_missing():
    try:
        PhishTank().fetch(days=1, settings=Settings())
    except MissingCredentialsError as exc:
        assert "phishtank_username" in exc.missing
    else:
        raise AssertionError("expected MissingCredentialsError")
