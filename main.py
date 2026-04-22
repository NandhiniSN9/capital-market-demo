"""Deal Intelligence Agent — Standalone Databricks App entry point."""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up DB connection at startup."""
    logger.info("[STARTUP] Initializing database engine...")
    try:
        from BE.models.db import get_engine
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[STARTUP] Database connection verified successfully")
    except Exception as e:
        logger.error("[STARTUP] Database warmup failed: %s", str(e))
    yield


from BE.routes import (
    chat_routes,
    conversation_routes,
    default,
    document_routes,
    message_routes,
    session_routes,
    stream_routes,
)

app = FastAPI(title="Deal Intelligence Agent", version="1.0.0", lifespan=lifespan)

# Request timing middleware — logs how long each request takes
import time as _time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = _time.perf_counter()
        response = await call_next(request)
        elapsed = _time.perf_counter() - start
        logger.info("[PERF] %s %s → %.2fs", request.method, request.url.path, elapsed)
        return response

app.add_middleware(TimingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
from BE.utils.exceptions.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.detail},
    )

# API routes
app.include_router(default.router, prefix="/api")
app.include_router(chat_routes.router, prefix="/api/v1")
app.include_router(conversation_routes.router, prefix="/api/v1")
app.include_router(document_routes.router, prefix="/api/v1")
app.include_router(message_routes.router, prefix="/api/v1")
app.include_router(session_routes.router, prefix="/api/v1")
app.include_router(stream_routes.router, prefix="/api/v1")

# Serve Deal React frontend
_static_dir = os.path.join(os.path.dirname(__file__), "BE", "static", "deal")
_assets_dir = os.path.join(_static_dir, "assets")
_index_html = os.path.join(_static_dir, "index.html")


@app.get("/assets/{file_path:path}")
def serve_static_asset(file_path: str):
    """Serve static assets with correct MIME types."""
    file_full = os.path.join(_assets_dir, file_path)
    if os.path.isfile(file_full):
        return FileResponse(file_full)
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """Catch-all: serve index.html for SPA routing."""
    if os.path.exists(_index_html):
        return FileResponse(_index_html)
    return {"message": "Deal Intelligence Agent API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
