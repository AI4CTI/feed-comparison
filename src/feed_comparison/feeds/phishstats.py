import json
import logging
import time
from datetime import datetime, timedelta

import pandas as pd

from feed_comparison.feeds._http import bounded_get
from feed_comparison.feeds.base import Feed
from feed_comparison.settings import Settings
from feed_comparison.utils.normalize import canonicalize_feed

_API_URL = "https://phishstats.info:2096/api/phishing?_sort=-date"
_REQUEST_DELAY_S = 3
_PROGRESS_EVERY_N_PAGES = 10
# Hard safety net against a server that keeps returning pages without
# advancing past the cutoff. Set very high so a legitimate, wide --days
# request never gets cut short. If it ever trips, the user sees a loud
# WARNING explaining the partial download.
_MAX_PAGES_SAFETY = 100_000
_log = logging.getLogger(__name__)


def _parse_date(s):
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in s else "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(s, fmt)


def _query_page(page):
    time.sleep(_REQUEST_DELAY_S)
    resp = bounded_get(f"{_API_URL}&_p={page}", timeout=60)
    if resp.status_code > 201:
        _log.warning(
            "PhishStats page %d returned HTTP %d (server-side issue, aborting)",
            page,
            resp.status_code,
        )
        return None
    try:
        return resp.json()
    except json.JSONDecodeError:
        _log.exception("PhishStats: failed to decode JSON for page %d", page)
        return None


def _fetch_raw(days):
    now_utc = datetime.utcnow()
    cutoff = now_utc - timedelta(days=days)
    rows = []
    page = 0
    oldest_seen = None
    while True:
        payload = _query_page(page)
        if payload is None:
            break
        page_rows = []
        oldest_in_page = None
        for entry in payload:
            d = _parse_date(entry["date"])
            page_rows.append({"url": entry["url"], "discovered_date": d})
            oldest_in_page = d if oldest_in_page is None else min(oldest_in_page, d)
        rows.extend(page_rows)
        if oldest_in_page is not None:
            oldest_seen = (
                oldest_in_page if oldest_seen is None else min(oldest_seen, oldest_in_page)
            )
        if not page_rows or (oldest_in_page is not None and oldest_in_page < cutoff):
            break
        page += 1
        if page % _PROGRESS_EVERY_N_PAGES == 0:
            if oldest_seen is not None:
                days_back = (now_utc - oldest_seen).total_seconds() / 86400
                coverage = (
                    f"oldest IoC at {oldest_seen.isoformat(timespec='seconds')} "
                    f"({days_back:.1f}/{days:.1f} days back)"
                )
            else:
                coverage = "no IoCs yet"
            _log.info(
                "PhishStats: %d pages, %d IoCs, %s",
                page,
                len(rows),
                coverage,
            )
        if page >= _MAX_PAGES_SAFETY:
            _log.warning(
                "PhishStats: hit MAX_PAGES_SAFETY=%d after %d IoCs; stopping. "
                "The downloaded window is INCOMPLETE — likely a misbehaving "
                "upstream server that does not advance past the cutoff. Try a "
                "smaller --days, or report the issue to PhishStats.",
                _MAX_PAGES_SAFETY,
                len(rows),
            )
            break

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df[df["discovered_date"] >= cutoff].reset_index(drop=True)


class PhishStats:
    name = "phishstats"
    short_name = "ps"
    homepage = "https://phishstats.info/"
    description = "Public phishing IoC feed (no credentials required)."
    requires_credentials: tuple[str, ...] = ()

    def fetch(self, days, settings: Settings, skip_recent_days: float = 0.0):
        # `skip_recent_days` is a hint we currently ignore: PhishStats
        # paginates newest-first, and acting on the hint would mean *skipping*
        # initial pages — the API has no way to start mid-feed, so we'd still
        # have to fetch them. The caller's post-fetch filter trims the window.
        raw = _fetch_raw(days)
        return canonicalize_feed(raw, self.short_name)


feed: Feed = PhishStats()
