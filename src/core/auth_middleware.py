from typing import Iterable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.api.modules.auth.service import AuthService


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        public_paths: Optional[Iterable[str]] = None,
        public_prefixes: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.public_paths = set(public_paths or [])
        self.public_prefixes = tuple(public_prefixes or [])

    def _is_public_path(self, path: str) -> bool:
        if path in self.public_paths:
            return True
        if self.public_prefixes and path.startswith(self.public_prefixes):
            return True
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if self._is_public_path(path):
            return await call_next(request)

        token = request.cookies.get("auth_token")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication cookie"},
            )

        payload = AuthService.verify_token(token, "access")
        if not payload or not payload.get("user_id"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired access token"},
            )

        request.state.user_id = int(payload["user_id"])
        return await call_next(request)
