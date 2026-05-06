import json
from pathlib import Path

import pytest

from feed_comparison.utils.canonicalize import canonical_url

CASES_FILE = Path(__file__).parent / "data" / "canonicalize_cases.json"
_CASES = json.loads(CASES_FILE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("raw_input", "expected"),
    [(c["input"], c["expected"]) for c in _CASES["partial"]],
    ids=[c["input"] for c in _CASES["partial"]],
)
def test_canonical_url_without_query(raw_input, expected):
    """parsed_url (return value [0]) drops the query string."""
    got = canonical_url(raw_input)[0].decode()
    assert got == expected


@pytest.mark.parametrize(
    ("raw_input", "expected"),
    [(c["input"], c["expected"]) for c in _CASES["full"]],
    ids=[c["input"] for c in _CASES["full"]],
)
def test_canonical_url_full(raw_input, expected):
    """full_parsed_url (return value [1]) keeps the (sorted) query string."""
    got = canonical_url(raw_input)[1].decode()
    assert got == expected
