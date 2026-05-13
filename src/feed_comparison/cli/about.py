"""`feed-comparison about` — project metadata, references and credits.

Reads its content from the package's installed metadata (so the version,
license, and URLs stay in sync with pyproject.toml automatically) plus a
small set of static fields that aren't expressible in standard packaging
metadata (funding source, affiliations, citation hint).
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from feed_comparison import __version__

# Static fields that don't fit neatly in pyproject metadata.
_REPO_URL = "https://github.com/AI4CTI/feed-comparison"
_ISSUES_URL = f"{_REPO_URL}/issues"
_CHANGELOG_URL = f"{_REPO_URL}/blob/main/CHANGELOG.md"
_TAGLINE = "A reproducible CLI to compare and benchmark malicious-URL threat intelligence feeds."
_LICENSE = "AGPL-3.0-or-later"
_MAINTAINER = "Stefano Traverso"
_AUTHORS = "Ermes Cyber Security S.p.A. · AI4CTI contributors"
_AFFILIATIONS = "Ermes Cyber Security · Politecnico di Torino"
_FUNDING = (
    "Italian Ministry of Education, Grant FISA-2023-00168\n"
    "(AI4CTI: AI for Cyber Threat Intelligence)"
)
_CITATION = "See CITATION.cff in the repository root"


def about() -> None:
    """Print project metadata, references and credits."""
    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", justify="right", no_wrap=True)
    table.add_column()

    table.add_row("Repository", _REPO_URL)
    table.add_row("Issues", _ISSUES_URL)
    table.add_row("Changelog", _CHANGELOG_URL)
    table.add_row("License", _LICENSE)
    table.add_row("", "")
    table.add_row("Maintainer", _MAINTAINER)
    table.add_row("Authors", _AUTHORS)
    table.add_row("", "")
    table.add_row("Affiliations", _AFFILIATIONS)
    table.add_row("Funding", _FUNDING)
    table.add_row("Citation", _CITATION)

    panel = Panel(
        table,
        title=f"feed-comparison v{__version__}",
        subtitle=_TAGLINE,
        border_style="red",
        padding=(1, 2),
    )
    console.print(panel)


# Wrapper for Typer registration with a clean docstring as command help.
def about_command():
    """Show project metadata, references and credits."""
    about()


# Allow `python -m feed_comparison.cli.about` for ad-hoc inspection.
if __name__ == "__main__":
    typer.run(about_command)
