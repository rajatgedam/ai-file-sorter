from fastapi import APIRouter
from pydantic import BaseModel

from src.lib.ollama_provider import OLLAMA_HOST, check_ollama_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_host: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    connected = check_ollama_connection()
    return HealthResponse(
        status="ok",
        ollama_connected=connected,
        ollama_host=OLLAMA_HOST,
    )
