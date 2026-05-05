# AI File Sorter — Plan & Progress

## Overview
A local AI-powered file sorter. The user picks a folder at runtime, the LLM (Ollama/llama3) analyzes file names (optionally content) and proposes a folder structure. The user reviews and approves before any files are moved.

**Stack:** Python 3.11+ / FastAPI backend · React + TypeScript / Vite frontend · Ollama (llama3 8B) running natively on Mac

---

## Architecture

```
file-sorter/
  TODO.md
  backend/
    main.py                  ← FastAPI app entry point
    requirements.txt
    .env.example
    src/
      types.py               ← Pydantic models
      routes/
        sort.py              ← POST /api/sort/analyze, POST /api/sort/execute
        health.py            ← GET /health
      lib/
        ollama_provider.py   ← LLM calls via ollama Python library
        file_scanner.py      ← Directory scanning, extension/mime detection
        file_mover.py        ← Dry-run + actual shutil.move logic
    tests/
      test_sort.py
  frontend/
    src/
      App.tsx
      App.css
      components/
        FolderInput.tsx      ← Path input + scan trigger + content toggle
        ProposalView.tsx     ← Per-file approve/reject table + Execute button
        ResultView.tsx       ← moved/skipped/error summary
      services/
        sortApi.ts           ← analyzeFolder(), executeSort()
```

## API Contract

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check Ollama connectivity |
| POST | `/api/sort/analyze` | Scan folder + get LLM proposals |
| POST | `/api/sort/execute` | Move approved files |

---

## To-Do Checklist

### Phase 1 — Backend Foundation
- [x] 1. Initialize `backend/` with `requirements.txt` (`fastapi`, `uvicorn`, `ollama`, `python-magic`, `pydantic`, `pytest`, `httpx`)
- [x] 2. Create `src/types.py` — Pydantic models: `ScanRequest`, `FileEntry`, `ProposedMove`, `SortProposal`, `ExecuteRequest`, `ExecuteResult`
- [x] 3. Create `src/lib/file_scanner.py` — list files, extract metadata, optional first-200-char snippets for text files
- [x] 4. Create `src/lib/ollama_provider.py` — call llama3, parse JSON proposals; model configurable via `OLLAMA_MODEL` env var
- [x] 5. Create `src/lib/file_mover.py` — `execute()` does `shutil.move()` with per-file error capture
- [x] 6. Create `src/routes/sort.py` — `POST /api/sort/analyze`, `POST /api/sort/execute`
- [x] 7. Create `src/routes/health.py` — `GET /health`, checks Ollama connectivity
- [x] 8. Create `main.py` — FastAPI app, CORS, route mounting
- [x] 9. Create `.env.example` — `OLLAMA_MODEL`, `OLLAMA_HOST`, `CORS_ORIGIN`

### Phase 2 — Backend Tests
- [x] 10. Write `tests/test_sort.py` using pytest — mock `ollama.chat` and file system calls
  - Happy path: analyze returns proposals ✅
  - Empty folder: returns empty proposals ✅
  - Execute: only moves `approved=True` items ✅
  - Execute: captures per-file errors without crashing ✅
  - Health: returns ok when Ollama reachable ✅
  - Coverage: **96%** (24/24 tests passing) ✅

### Phase 3 — Frontend
- [x] 11. Scaffold Vite + React + TypeScript in `frontend/`
- [x] 12. Create `src/services/sortApi.ts` — `analyzeFolder()`, `executeSort()`
- [x] 13. Create `FolderInput.tsx` — path input, Analyze button, include-content toggle
- [x] 14. Create `ProposalView.tsx` — per-row approve/reject checkboxes + Execute button
- [x] 15. Create `ResultView.tsx` — moved/skipped/error counts after execution
- [x] 16. Wire up `App.tsx` — 3-step flow: Input → Proposal → Result + error state
- [x] 17. Style `App.css` — single file, BEM-like naming

### Phase 4 — Integration & Config
- [x] 18. End-to-end smoke test: point at a real test folder, run full flow
- [x] 19. Add `docker-compose.yml` for backend containerization (Ollama stays native)
- [x] 20. Final pass: env vars documented, `.env.example` complete, verify ≥80% coverage

---

## Phase 5 — Low Effort Improvements

### Backend
- [x] 21. **Recursive folder scanning** — `recursive` flag on `ScanRequest`; uses `Path.rglob()`
- [x] 22. **Undo / rollback** — moves logged to `~/.ai-file-sorter/history.json`; `POST /api/sort/undo` reverses by session_id
- [x] 23. **Conflict handling** — destination existence checked; auto-renames with `(1)`, `(2)` suffix
- [x] 24. **Batch LLM for large folders** — files split into chunks of 50; proposals merged
- [x] 25. **Retry on bad JSON** — malformed LLM response retried once with correction prompt
- [x] 26. **`GET /api/models`** — calls `ollama.list()`, returns available local models
- [x] 27. Tests updated — 37/37 passing, 95% coverage

## Phase 6 — UI / UX Improvements

### Frontend
- [x] 28. **Native folder picker** — `window.showDirectoryPicker()` with graceful fallback on unsupported browsers
- [x] 29. **Proposal tree view** — moves grouped by destination folder, collapsible per-folder with folder-level select/deselect
- [x] 30. **Model picker** — `GET /api/models` called on load; dropdown shown when models available
- [x] 31. **Undo button in ResultView** — ↩ Undo moves button calls `POST /api/sort/undo` with session_id
- [ ] 32. **Execute progress** — per-file progress during execute (stream/poll)

---

## Key Decisions
- Ollama runs **natively on Mac** (not in Docker); backend calls `http://localhost:11434` by default, overridable via `OLLAMA_HOST`
- **File content reading is opt-in** (`include_content` flag); reads first 200 chars of text files only, skips binaries via mime type
- **No files move without approval** — `/execute` only processes moves where `approved=True`
- **No recursive scanning, no undo, no custom rules** in v1

---

## Progress Log

| Date | Item | Status | Notes |
|------|------|--------|-------|
| 2026-05-04 | Plan finalized | ✅ Done | Stack, architecture, API contract agreed |
| 2026-05-04 | Phase 1 — Backend Foundation | ✅ Done | FastAPI app, all lib modules, routes, .env.example |
| 2026-05-04 | Phase 2 — Backend Tests | ✅ Done | 24/24 tests passing, 96% coverage |
| 2026-05-04 | Phase 4 — Smoke test | ✅ Done | 10 files → 6 folders, 0 errors. Backend on :8001, frontend on :5173 |
| 2026-05-05 | Phase 5 — Low effort improvements | ✅ Done | Recursive scan, undo/rollback, conflict handling, LLM batching, retry, /api/models |
| 2026-05-05 | Phase 6 — UI/UX improvements | ✅ Done | Folder picker, tree view, model dropdown, undo button. 37 tests, 95% coverage |

