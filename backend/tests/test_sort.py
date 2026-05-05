import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from src.types import ProposedMove

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ollama_response(moves: list[dict]) -> MagicMock:
    """Build a mock ollama.Client().chat() return value."""
    mock_response = MagicMock()
    mock_response.__getitem__ = lambda self, key: (
        {"message": {"content": json.dumps(moves)}}[key]
    )
    return mock_response


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ollama_connected(self):
        with patch("src.routes.health.check_ollama_connection", return_value=True):
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ollama_connected"] is True

    def test_health_ollama_disconnected(self):
        with patch("src.routes.health.check_ollama_connection", return_value=False):
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ollama_connected"] is False


# ---------------------------------------------------------------------------
# /api/sort/analyze
# ---------------------------------------------------------------------------


class TestAnalyze:
    def test_analyze_happy_path(self, tmp_path: Path):
        """Scan a folder with files and get back proposed moves."""
        (tmp_path / "report.pdf").write_text("dummy")
        (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff")

        proposed = [
            {
                "source": str(tmp_path / "report.pdf"),
                "destination": str(tmp_path / "Documents" / "report.pdf"),
                "reason": "PDF documents go in Documents",
            },
            {
                "source": str(tmp_path / "photo.jpg"),
                "destination": str(tmp_path / "Images" / "photo.jpg"),
                "reason": "JPEG images go in Images",
            },
        ]

        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {"content": json.dumps(proposed)}
        }

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.post(
                "/api/sort/analyze",
                json={"folder_path": str(tmp_path), "include_content": False},
            )

        assert response.status_code == 200
        moves = response.json()["moves"]
        assert len(moves) == 2
        assert moves[0]["source"] == str(tmp_path / "report.pdf")
        assert moves[0]["approved"] is True

    def test_analyze_empty_folder(self, tmp_path: Path):
        """Empty folder returns empty moves list."""
        response = client.post(
            "/api/sort/analyze",
            json={"folder_path": str(tmp_path), "include_content": False},
        )
        assert response.status_code == 200
        assert response.json()["moves"] == []

    def test_analyze_invalid_path(self):
        """Non-existent folder returns 400."""
        response = client.post(
            "/api/sort/analyze",
            json={"folder_path": "/nonexistent/path/xyz", "include_content": False},
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_analyze_path_is_file(self, tmp_path: Path):
        """Passing a file path instead of a directory returns 400."""
        f = tmp_path / "file.txt"
        f.write_text("hello")
        response = client.post(
            "/api/sort/analyze",
            json={"folder_path": str(f), "include_content": False},
        )
        assert response.status_code == 400
        assert "not a directory" in response.json()["detail"]

    def test_analyze_llm_error_returns_502(self, tmp_path: Path):
        """LLM failure returns 502."""
        (tmp_path / "file.txt").write_text("hello")

        mock_client = MagicMock()
        mock_client.chat.side_effect = ConnectionError("Ollama not running")

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.post(
                "/api/sort/analyze",
                json={"folder_path": str(tmp_path), "include_content": False},
            )

        assert response.status_code == 502
        assert "LLM error" in response.json()["detail"]

    def test_analyze_with_content_includes_snippet(self, tmp_path: Path):
        """With include_content=True, text files have snippets sent to LLM."""
        notes = tmp_path / "notes.txt"
        notes.write_text("Meeting notes from Q1 review...")

        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {
                "content": json.dumps(
                    [
                        {
                            "source": str(notes),
                            "destination": str(tmp_path / "Notes" / "notes.txt"),
                            "reason": "Text notes go in Notes",
                        }
                    ]
                )
            }
        }

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.post(
                "/api/sort/analyze",
                json={"folder_path": str(tmp_path), "include_content": True},
            )

        assert response.status_code == 200
        # Verify snippet was included in the prompt
        call_args = mock_client.chat.call_args
        user_message = call_args[1]["messages"][1]["content"]
        assert "Meeting notes" in user_message


# ---------------------------------------------------------------------------
# /api/sort/execute
# ---------------------------------------------------------------------------


class TestExecute:
    def test_execute_moves_approved_files(self, tmp_path: Path):
        """Only approved=True moves are executed."""
        src_file = tmp_path / "photo.jpg"
        src_file.write_bytes(b"\xff\xd8\xff")
        dest = tmp_path / "Images" / "photo.jpg"

        response = client.post(
            "/api/sort/execute",
            json={
                "folder_path": str(tmp_path),
                "moves": [
                    {
                        "source": str(src_file),
                        "destination": str(dest),
                        "reason": "JPEG goes in Images",
                        "approved": True,
                    }
                ],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert str(src_file) in result["moved"]
        assert result["skipped"] == []
        assert result["errors"] == []
        assert dest.exists()

    def test_execute_skips_unapproved_files(self, tmp_path: Path):
        """approved=False moves are skipped and files not moved."""
        src_file = tmp_path / "photo.jpg"
        src_file.write_bytes(b"\xff\xd8\xff")
        dest = tmp_path / "Images" / "photo.jpg"

        response = client.post(
            "/api/sort/execute",
            json={
                "folder_path": str(tmp_path),
                "moves": [
                    {
                        "source": str(src_file),
                        "destination": str(dest),
                        "reason": "JPEG goes in Images",
                        "approved": False,
                    }
                ],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["moved"] == []
        assert str(src_file) in result["skipped"]
        assert not dest.exists()

    def test_execute_captures_missing_source_as_error(self, tmp_path: Path):
        """A move where the source file is missing is recorded as an error, not a crash."""
        response = client.post(
            "/api/sort/execute",
            json={
                "folder_path": str(tmp_path),
                "moves": [
                    {
                        "source": str(tmp_path / "ghost.txt"),
                        "destination": str(tmp_path / "Other" / "ghost.txt"),
                        "reason": "Missing file",
                        "approved": True,
                    }
                ],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["moved"] == []
        assert len(result["errors"]) == 1
        assert "ghost.txt" in result["errors"][0]

    def test_execute_mixed_approved_and_skipped(self, tmp_path: Path):
        """Mix of approved/unapproved moves handled correctly."""
        keep = tmp_path / "keep.txt"
        move_me = tmp_path / "report.pdf"
        keep.write_text("keep")
        move_me.write_text("report")

        response = client.post(
            "/api/sort/execute",
            json={
                "folder_path": str(tmp_path),
                "moves": [
                    {
                        "source": str(keep),
                        "destination": str(tmp_path / "Other" / "keep.txt"),
                        "reason": "Rejected by user",
                        "approved": False,
                    },
                    {
                        "source": str(move_me),
                        "destination": str(tmp_path / "Docs" / "report.pdf"),
                        "reason": "PDF to Docs",
                        "approved": True,
                    },
                ],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert str(move_me) in result["moved"]
        assert str(keep) in result["skipped"]
        assert keep.exists()  # not moved

    def test_execute_empty_moves_returns_400(self):
        response = client.post(
            "/api/sort/execute",
            json={"folder_path": "/some/path", "moves": []},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# File scanner unit tests
# ---------------------------------------------------------------------------


class TestFileScanner:
    def test_scan_lists_files(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.pdf").write_bytes(b"%PDF")

        entries = scan_directory(str(tmp_path))
        names = [e.name for e in entries]
        assert "a.txt" in names
        assert "b.pdf" in names

    def test_scan_excludes_directories(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.txt").write_text("hi")

        entries = scan_directory(str(tmp_path))
        assert all(e.name != "subdir" for e in entries)

    def test_scan_snippet_for_text_file(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        content = "A" * 300
        (tmp_path / "notes.txt").write_text(content)

        entries = scan_directory(str(tmp_path), include_content=True)
        assert entries[0].snippet is not None
        assert len(entries[0].snippet) <= 200

    def test_scan_raises_on_missing_path(self):
        from src.lib.file_scanner import scan_directory

        with pytest.raises(ValueError, match="does not exist"):
            scan_directory("/nonexistent/xyz")

    def test_scan_raises_on_file_path(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        f = tmp_path / "file.txt"
        f.write_text("hi")
        with pytest.raises(ValueError, match="not a directory"):
            scan_directory(str(f))


# ---------------------------------------------------------------------------
# Ollama provider unit tests
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    def test_propose_sort_returns_empty_for_no_files(self):
        from src.lib.ollama_provider import propose_sort

        result = propose_sort([], "/some/dir")
        assert result == []

    def test_propose_sort_parses_response(self, tmp_path: Path):
        from src.lib.ollama_provider import propose_sort
        from src.types import FileEntry

        files = [FileEntry(name="a.txt", path=str(tmp_path / "a.txt"), extension=".txt")]

        raw = json.dumps(
            [
                {
                    "source": str(tmp_path / "a.txt"),
                    "destination": str(tmp_path / "Text" / "a.txt"),
                    "reason": "Text file",
                }
            ]
        )

        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": raw}}

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            moves = propose_sort(files, str(tmp_path))

        assert len(moves) == 1
        assert moves[0].source == str(tmp_path / "a.txt")

    def test_propose_sort_strips_markdown_fences(self, tmp_path: Path):
        from src.lib.ollama_provider import propose_sort
        from src.types import FileEntry

        files = [FileEntry(name="a.txt", path=str(tmp_path / "a.txt"), extension=".txt")]

        raw = (
            "```json\n"
            + json.dumps(
                [
                    {
                        "source": str(tmp_path / "a.txt"),
                        "destination": str(tmp_path / "Text" / "a.txt"),
                        "reason": "Text file",
                    }
                ]
            )
            + "\n```"
        )

        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": raw}}

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            moves = propose_sort(files, str(tmp_path))

        assert len(moves) == 1

    def test_propose_sort_rejects_path_traversal(self, tmp_path: Path):
        from src.lib.ollama_provider import propose_sort
        from src.types import FileEntry

        files = [FileEntry(name="a.txt", path=str(tmp_path / "a.txt"), extension=".txt")]

        raw = json.dumps(
            [
                {
                    "source": str(tmp_path / "a.txt"),
                    "destination": "/etc/passwd",
                    "reason": "Malicious move",
                }
            ]
        )

        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": raw}}

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            with pytest.raises(ValueError, match="escapes base directory"):
                propose_sort(files, str(tmp_path))

    def test_check_ollama_connection_true(self):
        from src.lib.ollama_provider import check_ollama_connection

        mock_client = MagicMock()
        mock_client.list.return_value = []
        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            assert check_ollama_connection() is True

    def test_check_ollama_connection_false(self):
        from src.lib.ollama_provider import check_ollama_connection

        mock_client = MagicMock()
        mock_client.list.side_effect = ConnectionError("refused")
        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            assert check_ollama_connection() is False


# ---------------------------------------------------------------------------
# Recursive scanning
# ---------------------------------------------------------------------------


class TestRecursiveScanning:
    def test_scan_recursive_finds_nested_files(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (sub / "nested.pdf").write_bytes(b"%PDF")

        entries = scan_directory(str(tmp_path), recursive=True)
        names = [e.name for e in entries]
        assert "root.txt" in names
        assert "nested.pdf" in names

    def test_scan_non_recursive_excludes_nested_files(self, tmp_path: Path):
        from src.lib.file_scanner import scan_directory

        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (sub / "nested.pdf").write_bytes(b"%PDF")

        entries = scan_directory(str(tmp_path), recursive=False)
        names = [e.name for e in entries]
        assert "root.txt" in names
        assert "nested.pdf" not in names

    def test_analyze_endpoint_passes_recursive_flag(self, tmp_path: Path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "nested.txt").write_text("hi")

        proposed = [
            {
                "source": str(sub / "nested.txt"),
                "destination": str(tmp_path / "Text" / "nested.txt"),
                "reason": "Text file",
            }
        ]
        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": json.dumps(proposed)}}

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.post(
                "/api/sort/analyze",
                json={"folder_path": str(tmp_path), "include_content": False, "recursive": True},
            )

        assert response.status_code == 200
        assert len(response.json()["moves"]) == 1


# ---------------------------------------------------------------------------
# Conflict handling
# ---------------------------------------------------------------------------


class TestConflictHandling:
    def test_execute_renames_on_conflict(self, tmp_path: Path):
        from src.lib.file_mover import execute_moves
        from src.types import ProposedMove

        src = tmp_path / "report.pdf"
        src.write_text("new")
        dest = tmp_path / "Docs" / "report.pdf"
        dest.parent.mkdir(parents=True)
        dest.write_text("existing")  # pre-existing file

        result = execute_moves(
            [ProposedMove(source=str(src), destination=str(dest), reason="test", approved=True)]
        )

        assert len(result.moved) == 1
        assert len(result.errors) == 0
        # Original dest untouched; renamed file exists
        assert dest.exists()
        assert (tmp_path / "Docs" / "report(1).pdf").exists()

    def test_resolve_conflict_increments(self, tmp_path: Path):
        from src.lib.file_mover import _resolve_conflict

        dest = tmp_path / "file.txt"
        dest.write_text("a")
        (tmp_path / "file(1).txt").write_text("b")

        result = _resolve_conflict(dest)
        assert result.name == "file(2).txt"


# ---------------------------------------------------------------------------
# Undo / rollback
# ---------------------------------------------------------------------------


class TestUndo:
    def test_execute_returns_session_id(self, tmp_path: Path):
        src = tmp_path / "a.txt"
        src.write_text("hello")

        response = client.post(
            "/api/sort/execute",
            json={
                "folder_path": str(tmp_path),
                "moves": [
                    {
                        "source": str(src),
                        "destination": str(tmp_path / "Text" / "a.txt"),
                        "reason": "text",
                        "approved": True,
                    }
                ],
            },
        )
        assert response.status_code == 200
        assert response.json()["session_id"] is not None

    def test_undo_reverses_moves(self, tmp_path: Path):
        from src.lib.file_mover import HISTORY_FILE, execute_moves, undo_session
        from src.types import ProposedMove

        # Clean slate
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()

        src = tmp_path / "photo.jpg"
        src.write_text("img")
        dest = tmp_path / "Images" / "photo.jpg"

        result = execute_moves(
            [ProposedMove(source=str(src), destination=str(dest), reason="img", approved=True)]
        )
        assert dest.exists()
        assert not src.exists()

        undo_result = undo_session(result.session_id)
        assert len(undo_result.moved) == 1
        assert src.exists()
        assert not dest.exists()

    def test_undo_unknown_session_raises_404(self):
        response = client.post(
            "/api/sort/undo",
            json={"session_id": "nonexistent-uuid"},
        )
        assert response.status_code == 404

    def test_undo_removes_session_from_history(self, tmp_path: Path):
        from src.lib.file_mover import HISTORY_FILE, execute_moves, undo_session
        from src.types import ProposedMove

        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()

        src = tmp_path / "b.txt"
        src.write_text("data")
        dest = tmp_path / "Docs" / "b.txt"

        result = execute_moves(
            [ProposedMove(source=str(src), destination=str(dest), reason="doc", approved=True)]
        )
        undo_session(result.session_id)

        import json as _json
        history = _json.loads(HISTORY_FILE.read_text())
        assert not any(s["session_id"] == result.session_id for s in history)


# ---------------------------------------------------------------------------
# Batch LLM + retry
# ---------------------------------------------------------------------------


class TestBatchAndRetry:
    def test_large_folder_batches_llm_calls(self, tmp_path: Path):
        """51 files should trigger 2 LLM calls (batch size 50)."""
        from src.lib.ollama_provider import BATCH_SIZE, propose_sort
        from src.types import FileEntry

        files = [
            FileEntry(name=f"file{i}.txt", path=str(tmp_path / f"file{i}.txt"), extension=".txt")
            for i in range(BATCH_SIZE + 1)
        ]

        def make_response(batch):
            return {
                "message": {
                    "content": json.dumps(
                        [
                            {
                                "source": f.path,
                                "destination": str(tmp_path / "Text" / f.name),
                                "reason": "text",
                            }
                            for f in batch
                        ]
                    )
                }
            }

        mock_client = MagicMock()
        mock_client.chat.side_effect = [
            make_response(files[:BATCH_SIZE]),
            make_response(files[BATCH_SIZE:]),
        ]

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            moves = propose_sort(files, str(tmp_path))

        assert mock_client.chat.call_count == 2
        assert len(moves) == BATCH_SIZE + 1

    def test_retry_on_bad_json(self, tmp_path: Path):
        """First response is garbage JSON; second is valid — should succeed."""
        from src.lib.ollama_provider import propose_sort
        from src.types import FileEntry

        files = [FileEntry(name="a.txt", path=str(tmp_path / "a.txt"), extension=".txt")]
        valid_raw = json.dumps(
            [{"source": str(tmp_path / "a.txt"), "destination": str(tmp_path / "Text" / "a.txt"), "reason": "text"}]
        )

        mock_client = MagicMock()
        mock_client.chat.side_effect = [
            {"message": {"content": "this is not json!!!"}},
            {"message": {"content": valid_raw}},
        ]

        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            moves = propose_sort(files, str(tmp_path))

        assert len(moves) == 1
        assert mock_client.chat.call_count == 2


# ---------------------------------------------------------------------------
# GET /api/models
# ---------------------------------------------------------------------------


class TestModelsEndpoint:
    def test_models_returns_list(self):
        mock_client = MagicMock()
        mock_client.list.return_value = {
            "models": [
                {"name": "llama3:latest", "size": 4700000000},
                {"name": "mistral:latest", "size": 4100000000},
            ]
        }
        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.get("/api/models")

        assert response.status_code == 200
        models = response.json()["models"]
        assert len(models) == 2
        assert models[0]["name"] == "llama3:latest"

    def test_models_empty_when_none_pulled(self):
        mock_client = MagicMock()
        mock_client.list.return_value = {"models": []}
        with patch("src.lib.ollama_provider.ollama.Client", return_value=mock_client):
            response = client.get("/api/models")

        assert response.status_code == 200
        assert response.json()["models"] == []

