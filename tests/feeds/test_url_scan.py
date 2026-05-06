import responses

from feed_comparison.feeds.url_scan import UrlScan
from feed_comparison.settings import MissingCredentialsError, Settings

_BASE = "https://urlscan.io/api/v1/search/"


@responses.activate
def test_urlscan_returns_canonical_dataframe():
    payload = {
        "results": [
            {
                "page_url": "http://malicious-1.example.com/login",
                "date": "2026-04-29T12:00:00Z",
            },
            {
                "page_url": "http://malicious-2.example.com/",
                "date": "2026-04-29T13:00:00Z",
            },
        ]
    }
    responses.add(responses.GET, _BASE, json=payload, status=200, match_querystring=False)

    settings = Settings(urlscan_url=_BASE, urlscan_token="dummy")
    df = UrlScan().fetch(days=1, settings=settings)
    assert len(df) == 2
    assert {"hostname", "domain", "normURLwScheme"}.issubset(df.columns)


def test_urlscan_raises_when_credentials_missing():
    try:
        UrlScan().fetch(days=1, settings=Settings())
    except MissingCredentialsError as exc:
        assert "urlscan_url" in exc.missing
        assert "urlscan_token" in exc.missing
    else:
        raise AssertionError("expected MissingCredentialsError")
