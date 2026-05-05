import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.types import ExecuteResult, ProposedMove

HISTORY_FILE = Path(
    os.getenv("HISTORY_FILE", "~/.ai-file-sorter/history.json")
).expanduser()


def _resolve_conflict(destination: Path) -> Path:
    """
    If destination exists, append (1), (2), … until a free name is found.
    """
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _append_history(session_id: str, moves: list[dict]) -> None:
    """Persist executed moves to the history file for undo support."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            history = []
    history.append(
        {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "moves": moves,
        }
    )
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def execute_moves(moves: list[ProposedMove]) -> ExecuteResult:
    """
    Move files for every ProposedMove where approved=True.
    Handles destination conflicts by auto-renaming.
    Logs all executed moves to history for undo support.
    """
    moved: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    history_entries: list[dict] = []

    for move in moves:
        if not move.approved:
            skipped.append(move.source)
            continue

        source = Path(move.source)
        destination = _resolve_conflict(Path(move.destination))

        if not source.exists():
            errors.append(f"{move.source}: source file not found")
            continue

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append(move.source)
            history_entries.append(
                {"source": str(destination), "original": move.source}
            )
        except OSError as exc:
            errors.append(f"{move.source}: {exc}")

    session_id = str(uuid.uuid4())
    if history_entries:
        _append_history(session_id, history_entries)

    return ExecuteResult(
        moved=moved, skipped=skipped, errors=errors, session_id=session_id
    )


def undo_session(session_id: str) -> ExecuteResult:
    """
    Reverse all moves from a prior execute session by session_id.
    Moves files back from destination → original location.
    """
    if not HISTORY_FILE.exists():
        raise ValueError("No history found")

    history: list[dict] = json.loads(HISTORY_FILE.read_text())
    session = next((s for s in history if s["session_id"] == session_id), None)
    if not session:
        raise ValueError(f"Session {session_id} not found. It may have expired or never been created.")
    if session.get("undone"):
        raise ValueError(f"Session {session_id} was already undone. Your files have already been restored.")

    moved: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for entry in reversed(session["moves"]):
        source = Path(entry["source"])
        original = Path(entry["original"])

        if not source.exists():
            errors.append(f"{entry['source']}: file no longer exists, cannot undo")
            continue

        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(original))
            moved.append(str(source))
        except OSError as exc:
            errors.append(f"{entry['source']}: {exc}")

    # Mark session as undone (keep it so re-undo attempts get a clear message)
    for s in history:
        if s["session_id"] == session_id:
            s["undone"] = True
            break
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

    return ExecuteResult(moved=moved, skipped=skipped, errors=errors)

