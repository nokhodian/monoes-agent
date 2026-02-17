import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def error_envelope(message: str, code: str = "BadRequest", details: dict | None = None, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "requestId": str(uuid.uuid4())
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_envelope(message=str(exc.detail), code="HttpError", status_code=exc.status_code)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_envelope(message="Validation failed", code="ValidationError", details={"errors": exc.errors()}, status_code=422)

async def generic_exception_handler(request: Request, exc: Exception):
    return error_envelope(message="Internal server error", code="InternalError", status_code=500)
