from datetime import datetime, timedelta


def filter_off_last_days(downloaded_df, lastdaystoignore):
    cutoff = datetime.utcnow() - timedelta(hours=lastdaystoignore * 24)

    discovered_date_col = None
    for col in list(downloaded_df.columns):
        if "discovered_date" in col:
            discovered_date_col = col
    downloaded_df = downloaded_df[(downloaded_df[discovered_date_col] < cutoff)]

    return downloaded_df


def forces_temporal_boundaries(downloaded_dfs):
    max_bottom_date = None
    min_top_date = None
    for feed in downloaded_dfs:
        discovered_date_col = None
        for col in list(downloaded_dfs[feed].columns):
            if "discovered_date" in col:
                discovered_date_col = col
        max_bottom_date = downloaded_dfs[feed][discovered_date_col][-1]
        min_top_date = downloaded_dfs[feed][discovered_date_col][0]

    for feed in downloaded_dfs:
        discovered_date_col = None
        for col in list(downloaded_dfs[feed].columns):
            if "discovered_date" in col:
                discovered_date_col = col
        downloaded_dfs[feed] = downloaded_dfs[feed][
            (downloaded_dfs[feed][discovered_date_col] >= min_top_date)
            & (max_bottom_date >= downloaded_dfs[feed][discovered_date_col])
        ]
    return downloaded_dfs
