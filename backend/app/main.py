"""FastAPI application entry point.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs (Swagger) and /redoc
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.ml.predictor import predictor
from app.routers import (
    appliances,
    auth,
    chat,
    dashboard,
    expenses,
    issues,
    meta,
    notifications,
    predictions,
    schedules,
    users,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("homecare")


@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor.load()
    log.info("Predictor ready: %s", "Random Forest (synthetic-trained)" if predictor.ml_available else "rule-based")
    log.info("Assistant mode: %s", "LLM" if settings.llm_enabled else "rule-based fallback")
    yield


app = FastAPI(
    title="Predictive HomeCare AI API",
    description="REST API for the Smart Household Maintenance Manager. Use **Authorize** with a demo account "
                "(demo@homecare.ai / Demo@1234) to try authenticated endpoints.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        loc = ".".join(str(x) for x in e.get("loc", []) if x not in ("body", "query", "path"))
        msg = str(e.get("msg", "Invalid value")).removeprefix("Value error, ")
        errors.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(errors)})


@app.exception_handler(SQLAlchemyError)
async def db_handler(request: Request, exc: SQLAlchemyError):
    log.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "A database error occurred. Please try again."})


for r in (auth, users, dashboard, appliances, predictions, schedules, issues, expenses, notifications, chat, meta):
    app.include_router(r.router, prefix="/api")

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "ml_model": predictor.ml_available, "llm_enabled": settings.llm_enabled}
