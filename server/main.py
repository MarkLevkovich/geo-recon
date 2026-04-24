from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    template_dir: str = app.state.template_dir
    app.state.templates = Jinja2Templates(directory=template_dir)

    static_dir: str = f"{template_dir}/static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    yield


app: FastAPI = FastAPI(
    title="GeoRecon",
    description="Asynchronous geolocation capture service",
    lifespan=lifespan,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with clean JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with generic JSON response."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "detail": "Internal server error"},
    )


@app.get("/health", tags=["system"])
async def health_check(request: Request) -> dict[str, Any]:
    info_data = request.app.state.context
    session_dir = request.app.state.template_dir

    return {
        "status": "ok",
        "session_info": info_data,
        "session_dir": session_dir
    }


@app.get("/", tags=["frontend"])
async def serve_frontend(request: Request) -> Any:
    context: dict[str, Any] = getattr(request.app.state, "context", {})
    templates: Jinja2Templates = getattr(request.app.state, "templates")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )
