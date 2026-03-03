from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.features.projects import router as projects_router
from src.api.features.threads import router as threads_router
from src.api.schemas import error_response

app = FastAPI()

app.include_router(projects_router, prefix="/workspace")
app.include_router(threads_router, prefix="/workspace")


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Return standard error shape for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.detail)),
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    """Return standard error shape for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content=error_response(str(exc)),
    )


@app.get("/hello")
def read_root():
    return {"success": True, "message": "Hello, World!", "data": None}
