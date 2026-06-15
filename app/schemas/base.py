from typing import Any, Optional, List
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    detail: str
    error_code: Optional[str] = None
    errors: List[Any] = []


class ResponseModel(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: Any = None) -> "ResponseModel":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, detail: str, error_code: str = None, errors: list = None) -> "ResponseModel":
        return cls(
            success=False,
            error=ErrorDetail(detail=detail, error_code=error_code, errors=errors or []),
        )
