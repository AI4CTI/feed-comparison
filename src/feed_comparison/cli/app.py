import typer

import feed_comparison.feeds  # noqa: F401  -- import side-effect: populates the registry
from feed_comparison import __version__
from feed_comparison.cli._logging import configure_logging
from feed_comparison.cli.banner import print_banner
from feed_comparison.cli.compare import compare
from feed_comparison.cli.download import download
from feed_comparison.cli.list_feeds import list_feeds
from feed_comparison.cli.plot import plot_app


def _version_callback(value: bool):
    if value:
        typer.echo(f"feed-comparison {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="feed-comparison",
    help="Compare and benchmark malicious-URL threat intelligence feeds.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
    no_banner: bool = typer.Option(
        False,
        "--no-banner",
        help="Suppress the ASCII banner.",
        envvar="FEED_COMPARISON_NO_BANNER",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the program version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
):
    """feed-comparison root command — see subcommands below."""
    print_banner(suppress=no_banner)
    configure_logging(verbose)


app.command("list-feeds")(list_feeds)
app.command("download")(download)
app.command("compare")(compare)
app.add_typer(plot_app, name="plot")


if __name__ == "__main__":
    app()
