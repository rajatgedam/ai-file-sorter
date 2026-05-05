import shutil
from pathlib import Path

from src.types import ExecuteResult, ProposedMove


def execute_moves(moves: list[ProposedMove]) -> ExecuteResult:
    """
    Move files for every ProposedMove where approved=True.
    Skips unapproved moves. Captures per-file errors without raising.
    Returns an ExecuteResult summarising moved, skipped, and errored files.
    """
    moved: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for move in moves:
        if not move.approved:
            skipped.append(move.source)
            continue

        source = Path(move.source)
        destination = Path(move.destination)

        if not source.exists():
            errors.append(f"{move.source}: source file not found")
            continue

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append(move.source)
        except OSError as exc:
            errors.append(f"{move.source}: {exc}")

    return ExecuteResult(moved=moved, skipped=skipped, errors=errors)
