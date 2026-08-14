"""The README's subcommand table must list exactly what `binder-compare` ships.

Fifteen of the twenty-two subcommands had no human-facing documentation at all:
`analyze-target`, `mature`, `monomer`, `affinity` and `wetlab` existed only inside
`.claude/skills/` — agent instructions, not a manual — and `prefilter`, `qc-annotate`,
`epitope`, `epitope-map`, `beta-check`, `diversity`, `hits` and `validate` were
documented nowhere. Someone driving the pipeline from a terminal could not discover
them without reading `main.py`.

A table fixes that once; this test keeps it fixed. Drift runs both ways and both are
wrong: a new subcommand nobody documents is invisible, and a documented subcommand
that no longer exists sends a reader to an argparse error.
"""

import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("pandas")

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "Evaluator"))

_README = _ROOT / "README.md"
_HEADING = "#### All `binder-compare` subcommands"
# Table rows naming a subcommand: `| `extract` | … |`. Section-header rows
# (`| **Refolding** | |`) carry no code span and are skipped.
_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|", re.M)


def _shipped_subcommands() -> set[str]:
    """Every subcommand `binder-compare --help` offers, from the real parser."""
    import argparse

    from binder_comparison import main as bc_main

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    for name in dir(bc_main):
        mod = getattr(bc_main, name)
        if hasattr(mod, "add_parser") and getattr(mod, "__name__", "").startswith("binder_comparison.cli"):
            mod.add_parser(subs)
    return set(subs.choices)


def _documented_subcommands() -> set[str]:
    text = _README.read_text()
    start = text.index(_HEADING)
    rest = text[start + len(_HEADING) :]
    # The table ends at the next heading of the same or higher level.
    end = re.search(r"^#{1,4} ", rest, re.M)
    return set(_ROW.findall(rest[: end.start()] if end else rest))


def test_the_table_exists_and_is_not_empty():
    """Guard the parser so the real assertions below cannot pass vacuously."""
    assert _HEADING in _README.read_text(), "the subcommand table was removed"
    assert len(_documented_subcommands()) > 5


def test_every_shipped_subcommand_is_documented():
    missing = sorted(_shipped_subcommands() - _documented_subcommands())
    assert not missing, (
        f"binder-compare ships {missing} but README.md's subcommand table does not "
        f"list them — they are undiscoverable outside .claude/skills/ and main.py."
    )


def test_the_table_invents_nothing():
    extra = sorted(_documented_subcommands() - _shipped_subcommands())
    assert not extra, (
        f"README.md documents {extra}, which argparse does not accept — a reader "
        f"following the table gets 'invalid choice' and exit 2."
    )
