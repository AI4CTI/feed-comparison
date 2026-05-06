from datetime import datetime, timedelta


def _discovered_date_column(df):
    """Return the scalar 'discovered_date' column (i.e. NOT the plural list one)."""
    for col in df.columns:
        if col == "discovered_date" or col.startswith("discovered_date_"):
            return col
    raise ValueError("DataFrame has no 'discovered_date' column")


def filter_off_last_days(df, last_days_to_ignore):
    cutoff = datetime.utcnow() - timedelta(days=last_days_to_ignore)
    col = _discovered_date_column(df)
    return df[df[col] < cutoff]


def force_temporal_boundaries(downloaded_dfs):
    """Restrict every feed's DataFrame to the time window common to all feeds.

    The window is [max(min_per_feed), min(max_per_feed)]: the latest "earliest
    observation" across feeds and the earliest "latest observation" across
    feeds. Feeds are assumed to be sorted by ``discovered_date``.
    """
    if not downloaded_dfs:
        return downloaded_dfs

    earliest_per_feed = []
    latest_per_feed = []
    for df in downloaded_dfs.values():
        col = _discovered_date_column(df)
        earliest_per_feed.append(df[col].iloc[0])
        latest_per_feed.append(df[col].iloc[-1])

    window_start = max(earliest_per_feed)
    window_end = min(latest_per_feed)

    out = {}
    for feed, df in downloaded_dfs.items():
        col = _discovered_date_column(df)
        out[feed] = df[(df[col] >= window_start) & (df[col] <= window_end)]
    return out
