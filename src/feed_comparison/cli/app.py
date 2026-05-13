import os
import sys

import typer

import feed_comparison.feeds  # noqa: F401  -- import side-effect: populates the registry
from feed_comparison import __version__
from feed_comparison.cli._logging import configure_logging
from feed_comparison.cli.banner import print_banner
from feed_comparison.cli.compare import compare
from feed_comparison.cli.download import download
from feed_comparison.cli.list_feeds import list_feeds
from feed_comparison.cli.plot import plot_app

_BANNER_SUPPRESS_ENV_TRUTHY = {"1", "true", "yes", "on"}


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
    no_banner: bool = typer.Option(  # noqa: ARG001  shown in --help; consumed by main()
        False,
        "--no-banner",
        help="Suppress the ASCII banner. Also settable via FEED_COMPARISON_NO_BANNER=1.",
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
    # Banner is printed in main() BEFORE Typer parses args, so it also
    # shows on bare `feed-comparison` (which Typer short-circuits to help)
    # and on `--help`. The --no-banner option above stays here so it shows
    # up in `--help`; the actual suppression check is done in main().
    configure_logging(verbose)


def main():
    """Entry-point. Prints the banner before delegating to Typer.

    Typer's auto-help (triggered by `no_args_is_help=True` or `--help`)
    bypasses the root callback, so we cannot print the banner from there.
    Doing it at the entry-point level guarantees it shows on every
    interactive invocation, including bare `feed-comparison`.
    """
    args = sys.argv[1:]
    suppress = (
        "--no-banner" in args
        or "--version" in args  # scripts that parse `--version` shouldn't see decoration
        or os.environ.get("FEED_COMPARISON_NO_BANNER", "").lower() in _BANNER_SUPPRESS_ENV_TRUTHY
    )
    print_banner(suppress=suppress)
    # Strip --no-banner from argv so subcommands don't fail on an unknown flag.
    sys.argv = [a for a in sys.argv if a != "--no-banner"]
    app()


app.command("list-feeds")(list_feeds)
app.command("download")(download)
app.command("compare")(compare)
app.add_typer(plot_app, name="plot")


if __name__ == "__main__":
    main()
