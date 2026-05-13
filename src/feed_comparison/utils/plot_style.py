"""Shared visual style for SuperVenn and CDF time-delta plots.

Goals:
  * Make both plot families look like they belong to the same tool
    (same palette, same fonts, same grid, same axes treatment).
  * Pick a palette that survives both colour-blindness and B&W printing
    (Wong, 2011 — widely adopted in scientific publishing).
  * No new dependencies. We only tweak matplotlib's ``rcParams`` and ship
    a tiny helper to apply the style at plot time.

Usage:
    from feed_comparison.utils.plot_style import apply_style, WONG_PALETTE
    apply_style()
    # ... matplotlib / fastplot / supervenn calls below ...
"""

from cycler import cycler
from matplotlib import rcParams

# Wong (2011) — colour-blind safe, 8 colours.
# Reference: https://www.nature.com/articles/nmeth.1618
WONG_PALETTE = (
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#E69F00",  # orange
    "#F0E442",  # yellow
    "#000000",  # black
)

GRID_COLOR = "#e5e5e5"
SPINE_COLOR = "#333333"
TEXT_COLOR = "#222222"


def apply_style() -> None:
    """Set matplotlib rcParams to the project-wide visual style.

    Idempotent: calling twice has the same effect as once. Safe to call
    at the top of every plot helper without bookkeeping.
    """
    # Typography stack — graceful fallback chain. matplotlib silently
    # picks the first font available on the system; on a vanilla install
    # we always end up at DejaVu Sans.
    rcParams["font.family"] = "sans-serif"
    rcParams["font.sans-serif"] = [
        "Inter",
        "IBM Plex Sans",
        "Helvetica",
        "Arial",
        "DejaVu Sans",
    ]
    rcParams["font.size"] = 11
    rcParams["axes.titlesize"] = 13
    rcParams["axes.titleweight"] = "bold"
    rcParams["axes.labelsize"] = 11
    rcParams["axes.labelcolor"] = TEXT_COLOR
    rcParams["xtick.color"] = TEXT_COLOR
    rcParams["ytick.color"] = TEXT_COLOR

    # Axes treatment: keep bottom/left, drop top/right for a cleaner look.
    rcParams["axes.spines.top"] = False
    rcParams["axes.spines.right"] = False
    rcParams["axes.edgecolor"] = SPINE_COLOR
    rcParams["axes.linewidth"] = 1.0

    # Grid: light, behind the data.
    rcParams["axes.grid"] = True
    rcParams["axes.axisbelow"] = True
    rcParams["grid.color"] = GRID_COLOR
    rcParams["grid.linewidth"] = 0.8
    rcParams["grid.linestyle"] = "-"

    # Backgrounds: explicit white so we never inherit a transparent fig
    # that turns black on dark-mode README previews.
    rcParams["figure.facecolor"] = "white"
    rcParams["axes.facecolor"] = "white"
    rcParams["savefig.facecolor"] = "white"
    rcParams["savefig.edgecolor"] = "white"

    # Colour cycle.
    rcParams["axes.prop_cycle"] = cycler("color", WONG_PALETTE)

    # Output quality.
    rcParams["figure.dpi"] = 100  # on-screen
    rcParams["savefig.dpi"] = 150  # retina-friendly PNGs
    rcParams["savefig.bbox"] = "tight"

    # Legend.
    rcParams["legend.frameon"] = True
    rcParams["legend.framealpha"] = 0.85
    rcParams["legend.edgecolor"] = GRID_COLOR
    rcParams["legend.fontsize"] = 10
