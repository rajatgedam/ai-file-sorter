from fastapi import APIRouter, HTTPException

from src.lib.file_mover import execute_moves, undo_session
from src.lib.file_scanner import scan_directory
from src.lib.ollama_provider import propose_sort
from src.types import ExecuteRequest, ExecuteResult, ScanRequest, SortProposal, UndoRequest

router = APIRouter(prefix="/api/sort", tags=["sort"])


@router.post("/analyze", response_model=SortProposal)
async def analyze(request: ScanRequest) -> SortProposal:
    """Scan a folder and return AI-proposed file moves (dry-run only)."""
    try:
        files = scan_directory(
            request.folder_path,
            request.include_content,
            request.recursive,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        moves = propose_sort(files, request.folder_path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}")

    return SortProposal(moves=moves)


@router.post("/execute", response_model=ExecuteResult)
async def execute(request: ExecuteRequest) -> ExecuteResult:
    """Execute approved moves from a prior analyze call."""
    if not request.moves:
        raise HTTPException(status_code=400, detail="No moves provided")

    return execute_moves(request.moves)


@router.post("/undo", response_model=ExecuteResult)
async def undo(request: UndoRequest) -> ExecuteResult:
    """Reverse all moves from a prior execute session."""
    try:
        return undo_session(request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
