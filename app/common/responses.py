from fastapi import HTTPException, status

from app.common.logger import get_logger
from app.common.types import PkBaseModel

logger = get_logger()


class OkResponse(PkBaseModel):
    def __init__(self, **kwargs):
        response_str = str(kwargs)
        if not response_str:
            content = f"OK response with no content"
        elif len(response_str) > 70:
            content = f"OK response: {response_str[:70]}..."
        else:
            content = f"OK response: {response_str}"
        logger.info(content)
        super().__init__(**kwargs)


class ListModel[T](PkBaseModel):
    entities: list[T]


class ListResponse[T](ListModel[T]):
    def __init__(self, entities: list[T]):
        if not entities:
            content = "OK List response with no items"
        else:
            content = f"OK List response with {len(entities)} items."
        logger.info(content)
        super().__init__(entities=entities)


class MessageResponse(OkResponse):
    message: str


class IdResponse(OkResponse):
    id: str


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


class ConflictException(BaseErrorResponse):
    def __init__(self, detail: str | None = None):
        detail = f"Conflict: {detail}" if detail else "Conflict"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ResponseDocs:
    unauthorized_response = {
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {"example": {"detail": "Unauthorized: <reason>"}}
            },
        },
    }

    conflict_response = {
        409: {
            "description": "Conflict",
            "content": {
                "application/json": {"example": {"detail": "Conflict: <reason>"}}
            },
        },
    }

    forbidden_response = {
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {"example": {"detail": "Forbidden: <operation>"}}
            },
        },
    }
