from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

class AppException(Exception):
    """Base exception for all application-specific errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code or "INTERNAL_SERVER_ERROR"
        self.details = details
        super().__init__(message)

class EntityNotFoundException(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message, 
            status_code=status.HTTP_404_NOT_FOUND, 
            code="NOT_FOUND",
            details=details
        )

class AuthenticationError(AppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(
            message=message, 
            status_code=status.HTTP_401_UNAUTHORIZED, 
            code="UNAUTHORIZED",
            details=details
        )

class AuthorizationError(AppException):
    """Raised when a user does not have permission to perform an action."""
    def __init__(self, message: str = "Permission denied", details: Optional[Any] = None):
        super().__init__(
            message=message, 
            status_code=status.HTTP_403_FORBIDDEN, 
            code="FORBIDDEN",
            details=details
        )

class BadRequestException(AppException):
    """Raised for invalid client requests."""
    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(
            message=message, 
            status_code=status.HTTP_400_BAD_REQUEST, 
            code="BAD_REQUEST",
            details=details
        )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception handlers on the FastAPI application.
    Converts custom AppExceptions into consistent JSON responses.
    """
    @app.exception_handler(AppException)
    def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        content: Dict[str, Any] = {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
        if exc.details is not None:
            content["error"]["details"] = exc.details
            
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )

    @app.exception_handler(Exception)
    def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the raw exception here for debugging
        # import logging
        # logging.getLogger(__name__).error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred on the server.",
                    "details": str(exc) if app.debug else None
                }
            }
        )
