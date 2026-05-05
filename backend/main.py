import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.health import router as health_router
from src.routes.sort import router as sort_router

app = FastAPI(title="AI File Sorter", version="1.0.0")

cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sort_router)


@app.get("/")
async def root() -> dict:
    return {"message": "AI File Sorter API", "docs": "/docs"}
