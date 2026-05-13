"""apply_style() must set the project-wide visual contract: Wong palette,
clean axes, grid behind data. The exact rcParams values are tested so a
silent regression (someone bumping matplotlib defaults, or removing a
key from the helper) gets caught."""

from cycler import cycler
from matplotlib import rcParams

from feed_comparison.utils.plot_style import (
    GRID_COLOR,
    SPINE_COLOR,
    TEXT_COLOR,
    WONG_PALETTE,
    apply_style,
)


def test_apply_style_sets_wong_palette_as_color_cycle():
    apply_style()
    cyc = rcParams["axes.prop_cycle"]
    assert cyc == cycler("color", WONG_PALETTE)


def test_apply_style_drops_top_and_right_spines():
    apply_style()
    assert rcParams["axes.spines.top"] is False
    assert rcParams["axes.spines.right"] is False
    assert rcParams["axes.edgecolor"] == SPINE_COLOR


def test_apply_style_grid_is_light_and_behind_data():
    apply_style()
    assert rcParams["axes.grid"] is True
    assert rcParams["axes.axisbelow"] is True
    assert rcParams["grid.color"] == GRID_COLOR


def test_apply_style_uses_white_backgrounds_explicitly():
    """Avoids the dark-mode README surprise where transparent figures turn
    invisible against a dark background."""
    apply_style()
    assert rcParams["figure.facecolor"] == "white"
    assert rcParams["axes.facecolor"] == "white"
    assert rcParams["savefig.facecolor"] == "white"


def test_apply_style_savefig_dpi_is_retina_friendly():
    apply_style()
    assert rcParams["savefig.dpi"] >= 144  # roughly 2× the 72 dpi baseline


def test_apply_style_text_colors_are_readable():
    apply_style()
    assert rcParams["axes.labelcolor"] == TEXT_COLOR
    assert rcParams["xtick.color"] == TEXT_COLOR


def test_apply_style_is_idempotent():
    apply_style()
    first_palette = rcParams["axes.prop_cycle"]
    apply_style()
    second_palette = rcParams["axes.prop_cycle"]
    assert first_palette == second_palette


def test_wong_palette_has_eight_distinct_colors():
    assert len(WONG_PALETTE) == 8
    assert len(set(WONG_PALETTE)) == 8
