import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


def get_logger() -> logging.Logger:
    return logging.getLogger("uvicorn.error")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else "unknown"
        method = request.method
        endpoint = request.url.path
        get_logger().info(f'{client_ip}:{client_port} - "{method} {endpoint}" RECEIVED')
        response = await call_next(request)
        return response
