from fastapi import HTTPException, status

from app.common.logger import get_logger
from app.common.types import PkBaseModel

logger = get_logger()


class MessageResponse(PkBaseModel):
    message: str


class BaseErrorResponse(HTTPException):
    def __init__(self, status_code: int, detail: str):
        logger.warning(f"{status_code} Error response: {detail}")
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(BaseErrorResponse):
    def __init__(self, reason: str | None = None):
        detail = f"Unauthorized: {reason}" if reason else "Unauthorized"
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenOperationException(BaseErrorResponse):
    def __init__(self, operation: str | None = None):
        detail = f"Forbidden operation: {operation}" if operation else "Forbidden"
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InternalServerErrorException(BaseErrorResponse):
    def __init__(self, detail: str | None = None):
        detail = (
            f"Internal server error: {detail}" if detail else "Internal server error"
        )
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class NotImplementedException(BaseErrorResponse):
    def __init__(self, detail: str | None = None):
        detail = f"Not implemented: {detail}" if detail else "Not implemented"
        super().__init__(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)
