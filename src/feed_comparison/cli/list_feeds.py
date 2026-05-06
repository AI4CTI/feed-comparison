import json as jsonlib

import typer
from rich.console import Console
from rich.table import Table

from feed_comparison.feeds.registry import registry

console = Console()


def list_feeds(
    with_credentials: bool = typer.Option(
        False, "--with-credentials", help="Show only feeds that require credentials."
    ),
    json_out: bool = typer.Option(
        False, "--json", help="Print the feed catalogue as JSON instead of a table."
    ),
):
    """List the threat-intelligence feeds supported by this build."""
    feeds = registry.all()
    if with_credentials:
        feeds = [f for f in feeds if f.requires_credentials]

    if json_out:
        payload = [
            {
                "name": f.name,
                "short_name": f.short_name,
                "homepage": f.homepage,
                "description": f.description,
                "requires_credentials": list(f.requires_credentials),
            }
            for f in feeds
        ]
        console.print_json(jsonlib.dumps(payload))
        return

    table = Table(title="feed-comparison: supported feeds")
    table.add_column("Name", style="bold")
    table.add_column("Short")
    table.add_column("Credentials", style="yellow")
    table.add_column("Homepage", style="cyan", no_wrap=False)
    table.add_column("Description")

    for f in feeds:
        creds = ", ".join(c.upper() for c in f.requires_credentials) or "—"
        table.add_row(f.name, f.short_name, creds, f.homepage, f.description)

    console.print(table)
