"""Lazy Captain — FastAPI application."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from config import settings
from db import init_db
from routers import entries, suggestions, daily_meta, connectors


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Lazy Captain",
    description="AI-powered managerial impact logging — the captain sits back, AI does the work",
    version="0.1.0",
    lifespan=lifespan,
)

# API routers
app.include_router(entries.router, prefix="/api", tags=["entries"])
app.include_router(suggestions.router, prefix="/api", tags=["suggestions"])
app.include_router(daily_meta.router, prefix="/api", tags=["daily_meta"])
app.include_router(connectors.router, prefix="/api", tags=["connectors"])

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", settings.port))
    uvicorn.run("main:app", host=settings.host, port=port, reload=True)
