"""
Application-wide error classes and FastAPI exception handler.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Standard application error with HTTP status code."""
    def __init__(self, status_code: int = 400, detail: str = "שגיאה"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "הפריט לא נמצא"):
        super().__init__(404, detail)


class ValidationError(AppException):
    def __init__(self, detail: str = "נתונים לא תקינים"):
        super().__init__(422, detail)


class ConflictError(AppException):
    def __init__(self, detail: str = "פעולה סותרת"):
        super().__init__(409, detail)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global exception handler registered on the FastAPI app."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
