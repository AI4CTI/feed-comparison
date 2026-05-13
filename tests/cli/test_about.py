"""The `about` subcommand prints project metadata and credits — make
sure the key fields (repo URL, license, funding, maintainer) actually
appear in the output, so a refactor that drops one of them gets
caught immediately."""

from typer.testing import CliRunner

from feed_comparison.cli.app import app

runner = CliRunner()


def test_about_command_prints_essential_fields():
    """All the fields a downstream consumer typically looks for must be present."""
    result = runner.invoke(app, ["about"])
    assert result.exit_code == 0
    out = result.stdout
    # Identity
    assert "feed-comparison" in out
    assert "AGPL-3.0-or-later" in out
    # Repository pointers
    assert "github.com/AI4CTI/feed-comparison" in out
    # Credits
    assert "Stefano Traverso" in out
    assert "Ermes" in out
    assert "Politecnico di Torino" in out
    # Funding (mandatory mention for the publicly-funded research project)
    assert "FISA-2023-00168" in out
    # Citation hint
    assert "CITATION.cff" in out
