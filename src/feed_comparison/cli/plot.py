import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import typer

from feed_comparison.utils.plots import plot_supervenn, plot_timeplot

_log = logging.getLogger(__name__)

plot_app = typer.Typer(help="Re-render plots from previously saved CSV exports.")


def _feed_name_from_csv_path(path: Path) -> str:
    # Files written by `download`/`compare` follow:
    #   dataframe_<feed>_<days>_<run_id>.csv
    parts = path.stem.split("_")
    if len(parts) < 4 or parts[0] != "dataframe":
        raise ValueError(
            f"Unexpected CSV filename layout: {path.name!r}. "
            "Expected 'dataframe_<feed>_<days>_<run_id>.csv'."
        )
    # The feed name is everything between 'dataframe' and the days field.
    # Days is parsed from the right to be tolerant of feed names containing
    # underscores in the future.
    days_idx = next(i for i in range(len(parts) - 1, 0, -1) if _looks_like_days(parts[i]))
    return "_".join(parts[1:days_idx])


def _looks_like_days(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def _load_csv(path: Path) -> tuple[str, pd.DataFrame]:
    feed = _feed_name_from_csv_path(path)
    df = pd.read_csv(
        path, sep=",", header="infer", index_col="normURLwoScheme", on_bad_lines="skip"
    )
    return feed, df


@plot_app.command("supervenn")
def supervenn_cmd(
    inputs: list[Path] = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    metric: str = typer.Option("hostname", "--metric", help="hostname | domain | normURLwScheme"),
    output_dir: Path = typer.Option(Path("./output"), "--output-dir", "-o"),
):
    """Re-render a SuperVenn plot from previously saved CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {}
    for p in inputs:
        feed, df = _load_csv(p)
        downloaded[feed] = df
    run_id = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    plot_supervenn(list(downloaded.keys()), downloaded, metric, str(output_dir), "replot", run_id)


@plot_app.command("cdf")
def cdf_cmd(
    inputs: list[Path] = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    benchmark: str = typer.Option(..., "--benchmark", "-b", help="Reference feed name."),
    output_dir: Path = typer.Option(Path("./output"), "--output-dir", "-o"),
):
    """Re-render the time-delta CDF from previously saved CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {}
    for p in inputs:
        feed, df = _load_csv(p)
        downloaded[feed] = df
    run_id = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    plot_timeplot(benchmark, list(downloaded.keys()), downloaded, str(output_dir), "replot", run_id)
