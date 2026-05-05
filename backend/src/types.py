from pydantic import BaseModel


class ScanRequest(BaseModel):
    folder_path: str
    include_content: bool = False
    recursive: bool = False


class FileEntry(BaseModel):
    name: str
    path: str
    extension: str
    snippet: str | None = None


class ProposedMove(BaseModel):
    source: str
    destination: str
    reason: str
    approved: bool = True


class SortProposal(BaseModel):
    moves: list[ProposedMove]


class ExecuteRequest(BaseModel):
    folder_path: str
    moves: list[ProposedMove]


class ExecuteResult(BaseModel):
    moved: list[str]
    skipped: list[str]
    errors: list[str]
    session_id: str | None = None


class UndoRequest(BaseModel):
    session_id: str


class OllamaModel(BaseModel):
    name: str
    size: int | None = None


class ModelsResponse(BaseModel):
    models: list[OllamaModel]
