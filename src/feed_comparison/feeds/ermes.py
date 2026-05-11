import logging
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import pandas as pd

from feed_comparison.feeds.base import Feed
from feed_comparison.settings import (
    FeedConfigurationError,
    MissingOptionalDependencyError,
    Settings,
)
from feed_comparison.utils.normalize import canonicalize_feed

_log = logging.getLogger(__name__)

_PER_REQUEST = 50
_PROGRESS_EVERY_N_PAGES = 10
# Hard safety net: a buggy or hostile server that keeps returning pages
# without ever advancing the cursor would otherwise loop forever. Set
# very high so an honest server with a wide --days window is never cut
# short. If this ever trips, the user sees a loud WARNING.
_MAX_PAGES_SAFETY = 100_000


def _parse_iso8601(value):
    """Parse an ISO 8601 timestamp into a tz-naive UTC datetime.

    The Ermes feed emits offset-aware timestamps (`...Z` or `+HH:MM`).
    Every other feed in this tool stores `discovered_date` as tz-naive
    UTC, so we normalise here to keep them all comparable — otherwise
    pandas refuses to subtract aware from naive in the time-delta CDF.
    """
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _iocs_to_rows(meta_iter):
    """Map an iterable of `ermes_metadata` dicts to DataFrame-ready rows."""
    rows = []
    for meta in meta_iter:
        url = meta.get("url")
        if not url:
            continue
        discovered = meta.get("discovered")
        if not discovered:
            continue
        threat_types = meta.get("threat_types") or []
        rows.append(
            {
                "url": url,
                "discovered_date": _parse_iso8601(discovered),
                "confidence": meta.get("confidence"),
                "threat_type": threat_types[0] if threat_types else None,
                "target": meta.get("target"),
            }
        )
    return rows


def _fetch_raw(days, api_server, client_id, client_secret):
    try:
        from requests import HTTPError
        from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
        from requests_oauth2client.exceptions import OAuth2Error
        from taxii2client import ApiRoot
        from taxii2client.v21 import as_pages
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "ermes", ["taxii2-client", "requests-oauth2client"]
        ) from exc

    api_server = api_server.rstrip("/")
    token_endpoint = f"{api_server}/oauth/token"
    feed_url = f"{api_server}/public/v1/phishing"

    oauth = OAuth2Client(
        token_endpoint=token_endpoint,
        client_id=client_id,
        client_secret=client_secret,
    )
    auth = OAuth2ClientCredentialsAuth(oauth)
    api_root = ApiRoot(feed_url, auth=auth)

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

    rows = []
    try:
        collection = api_root.collections[0]
        pages = as_pages(
            collection.get_objects,
            per_request=_PER_REQUEST,
            added_after=cutoff.isoformat(),
        )
        for page_num, page in enumerate(pages, start=1):
            metas = (obj.get("ermes_metadata", {}) for obj in page.get("objects", []))
            rows.extend(_iocs_to_rows(metas))
            if page_num % _PROGRESS_EVERY_N_PAGES == 0:
                _log.info(
                    "Ermes feed: fetched %d pages, %d IoCs collected so far",
                    page_num,
                    len(rows),
                )
            if page_num >= _MAX_PAGES_SAFETY:
                _log.warning(
                    "Ermes feed: hit MAX_PAGES_SAFETY=%d after %d IoCs; stopping. "
                    "The downloaded window is INCOMPLETE — likely a misbehaving "
                    "upstream server. Try a smaller --days, or report the issue "
                    "to the Ermes CTI Feed maintainers.",
                    _MAX_PAGES_SAFETY,
                    len(rows),
                )
                break
    except OAuth2Error as exc:
        raise FeedConfigurationError(
            f"Ermes OAuth authentication against {token_endpoint} failed: {exc}. "
            "Verify ERMES_API_SERVER, ERMES_CLIENT_ID and ERMES_CLIENT_SECRET."
        ) from exc
    except HTTPError as exc:
        if exc.response is None or exc.response.status_code != HTTPStatus.NOT_FOUND:
            raise
        _log.debug("Ermes feed: server returned 404 (no more pages), stopping")

    return pd.DataFrame(rows)


class Ermes:
    name = "ermes"
    short_name = "er"
    homepage = "https://www.ermes.company/"
    description = "Ermes CTI Feed over STIX/TAXII (OAuth 2.0 Client Credentials)."
    requires_credentials: tuple[str, ...] = (
        "ermes_api_server",
        "ermes_client_id",
        "ermes_client_secret",
    )

    def fetch(self, days, settings: Settings):
        api_server, client_id, client_secret = settings.require(*self.requires_credentials)
        raw = _fetch_raw(days, api_server, client_id, client_secret)
        return canonicalize_feed(raw, self.short_name)


feed: Feed = Ermes()
