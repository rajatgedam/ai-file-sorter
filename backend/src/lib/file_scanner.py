import os
from pathlib import Path

from src.types import FileEntry

# Mime types considered plain text (safe to read snippets from)
TEXT_MIME_PREFIXES = ("text/",)
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".log", ".py", ".js", ".ts",
    ".jsx", ".tsx", ".html", ".css", ".sh", ".env",
}
SNIPPET_CHARS = 200


def _is_text_file(path: Path) -> bool:
    """Return True if the file is likely readable plain text."""
    try:
        import magic  # type: ignore

        mime = magic.from_file(str(path), mime=True)
        return any(mime.startswith(p) for p in TEXT_MIME_PREFIXES)
    except Exception:
        # Fall back to extension check if libmagic is unavailable
        return path.suffix.lower() in TEXT_EXTENSIONS


def _read_snippet(path: Path) -> str | None:
    """Read the first SNIPPET_CHARS characters of a text file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(SNIPPET_CHARS)
    except OSError:
        return None


def scan_directory(folder_path: str, include_content: bool = False) -> list[FileEntry]:
    """
    List all files (non-recursive) in folder_path.
    Returns a list of FileEntry objects.
    Raises ValueError if the path does not exist or is not a directory.
    """
    target = Path(folder_path).expanduser().resolve()

    if not target.exists():
        raise ValueError(f"Path does not exist: {folder_path}")
    if not target.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    entries: list[FileEntry] = []

    for item in sorted(target.iterdir()):
        if not item.is_file():
            continue

        snippet: str | None = None
        if include_content and _is_text_file(item):
            snippet = _read_snippet(item)

        entries.append(
            FileEntry(
                name=item.name,
                path=str(item),
                extension=item.suffix.lower(),
                snippet=snippet,
            )
        )

    return entries
