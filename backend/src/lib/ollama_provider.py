import json
import os
from pathlib import Path

import ollama

from src.types import FileEntry, OllamaModel, ProposedMove

DEFAULT_MODEL = "llama3"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
BATCH_SIZE = 50  # max files per LLM call

_SYSTEM_PROMPT = """You are a file organization assistant.
Given a list of files and their metadata, propose a folder structure to organize them.
Respond ONLY with a valid JSON array. Each element must have exactly these keys:
  "source"      - the original absolute file path (copy from input exactly)
  "destination" - the proposed absolute destination path including the new filename
  "reason"      - a short plain-English reason for this placement (max 20 words)

Rules:
- destination folders must be sub-folders of the original directory
- do not rename files, only move them into sub-folders
- every source file must appear exactly once in the output
- folder names must use CamelCase (e.g. "BackupFiles", "PdfDocuments", "DevProjects")
- output must be valid JSON only, no markdown fences, no commentary"""

_RETRY_PROMPT = (
    "Your previous response was not valid JSON. "
    "Respond ONLY with the JSON array, no other text."
)


def _build_user_prompt(files: list[FileEntry]) -> str:
    lines = []
    for f in files:
        line = f"- {f.path} (extension: {f.extension or 'none'})"
        if f.snippet:
            preview = f.snippet.replace("\n", " ")[:100]
            line += f" | preview: {preview}"
        lines.append(line)
    return "Organize these files:\n" + "\n".join(lines)


def _parse_proposals(raw: str, base_dir: str) -> list[ProposedMove]:
    """Parse the LLM JSON response into ProposedMove objects."""
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.startswith("```")
        ).strip()

    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array from LLM")

    moves: list[ProposedMove] = []
    base = Path(base_dir).expanduser().resolve()

    for item in data:
        destination = Path(item["destination"]).resolve()
        if not str(destination).startswith(str(base)):
            raise ValueError(
                f"Proposed destination escapes base directory: {destination}"
            )
        moves.append(
            ProposedMove(
                source=item["source"],
                destination=str(destination),
                reason=item.get("reason", ""),
                approved=True,
            )
        )

    return moves


def _call_llm(client: ollama.Client, messages: list[dict]) -> str:
    """Call the LLM with retry on malformed JSON."""
    response = client.chat(model=OLLAMA_MODEL, messages=messages)
    raw = response["message"]["content"]

    # Attempt parse; retry once if malformed
    try:
        _parse_proposals(raw, "/")  # dummy base just to check JSON validity
    except (json.JSONDecodeError, KeyError):
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": _RETRY_PROMPT},
        ]
        response = client.chat(model=OLLAMA_MODEL, messages=retry_messages)
        raw = response["message"]["content"]

    return raw


def propose_sort(files: list[FileEntry], base_dir: str) -> list[ProposedMove]:
    """
    Ask the LLM to propose folder moves for the given files.
    Batches files in groups of BATCH_SIZE.
    Returns a list of ProposedMove objects.
    """
    if not files:
        return []

    client = ollama.Client(host=OLLAMA_HOST)
    all_moves: list[ProposedMove] = []

    for i in range(0, len(files), BATCH_SIZE):
        batch = files[i : i + BATCH_SIZE]
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(batch)},
        ]
        raw = _call_llm(client, messages)
        all_moves.extend(_parse_proposals(raw, base_dir))

    return all_moves


def list_models() -> list[OllamaModel]:
    """Return all locally available Ollama models."""
    client = ollama.Client(host=OLLAMA_HOST)
    response = client.list()
    models = response.get("models", [])
    return [
        OllamaModel(
            name=m.get("name", m.get("model", "")),
            size=m.get("size"),
        )
        for m in models
    ]


def check_ollama_connection() -> bool:
    """Return True if Ollama is reachable."""
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        client.list()
        return True
    except Exception:
        return False
