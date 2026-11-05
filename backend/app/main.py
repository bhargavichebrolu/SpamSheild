"""Create the FastAPI application.

The model is loaded once at startup. If it can't be used, the API still starts, so that
/api/health can explain the problem, and the other endpoints return a clear 503.

Run from the backend folder:
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.routes import ClassificationFailed, router
from app.config import ALLOWED_ORIGINS, MAX_BODY_BYTES, MAX_DISCARD_BYTES, MAX_INPUT_CHARS
from app.ml.predict import ClassificationRejected, LoadedModel, ModelUnavailable, load_verified_model

logger = logging.getLogger("spamshield.api")

_TOO_LARGE_MESSAGE = (
    f"The request is too large. Send up to {MAX_INPUT_CHARS:,} characters of text."
)

# Maps Pydantic's error types to this API's codes and messages. The messages are fixed,
# because Pydantic's own errors repeat the rejected input, which could be someone's email.
_VALIDATION_ERRORS = {
    "missing": ("text_missing", "The request needs a 'text' field."),
    "string_type": ("text_not_a_string", "The 'text' field must be a string."),
    "text_empty": ("text_empty", "The text is empty. Enter some email text to classify."),
    "string_too_long": ("text_too_long", f"The text is longer than the {MAX_INPUT_CHARS:,} character limit."),
    "json_invalid": ("invalid_json", "The request body isn't valid JSON."),
    "model_attributes_type": ("invalid_body", "The request body must be a JSON object with a 'text' field."),
}


def _error_response(status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "field": field}},
    )


class BodySizeLimitMiddleware:
    """Reject request bodies over a size limit, before they're parsed.

    It counts the bytes actually received, so a request can't avoid the limit by
    leaving out or understating its Content-Length header.

    Before responding, it reads and discards the rest of the upload, up to a cap. If the
    server replied while a client was still sending, the connection would be reset, and
    the client would see a network failure instead of this error.
    """

    def __init__(self, app, max_bytes: int, max_discard_bytes: int = MAX_DISCARD_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.max_discard_bytes = max_discard_bytes

    async def _discard_rest_of_upload(self, receive) -> None:
        discarded = 0
        while discarded <= self.max_discard_bytes:
            message = await receive()
            discarded += len(message.get("body", b""))
            if message["type"] == "http.disconnect" or not message.get("more_body", False):
                return

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length", b"0")
        if declared.isdigit() and int(declared) > self.max_bytes:
            await self._discard_rest_of_upload(receive)
            await self._reject(scope, receive, send)
            return

        body = bytearray()
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            more_body = message.get("more_body", False)
            if len(body) > self.max_bytes:
                if more_body:
                    await self._discard_rest_of_upload(receive)
                await self._reject(scope, receive, send)
                return

        delivered = False

        async def replay_body():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay_body, send)

    @staticmethod
    async def _reject(scope, receive, send) -> None:
        response = _error_response(413, "body_too_large", _TOO_LARGE_MESSAGE)
        await response(scope, receive, send)


def create_app(model_loader: Callable[[], LoadedModel] = load_verified_model) -> FastAPI:
    """Build the application. Tests can pass a different loader to use a small model."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.model = None
        app.state.model_error = None
        try:
            app.state.model = model_loader()
        except ModelUnavailable as unavailable:
            app.state.model_error = str(unavailable)
            logger.error("Model unavailable: %s", unavailable)
        yield

    app = FastAPI(
        title="SpamShield AI API",
        version="1.0.0",
        description=(
            "Classifies email text as spam or ham, and explains the score. This is a learning "
            "and research prototype, not an email security product. Message text isn't stored or logged."
        ),
        lifespan=lifespan,
    )

    # Middleware added last runs first, so CORS headers also reach body-size rejections.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        first = error.errors()[0]
        code, message = _VALIDATION_ERRORS.get(
            first["type"], ("invalid_request", "The request isn't valid.")
        )
        field = "text" if "text" in first["loc"] else None
        return _error_response(422, code, message, field)

    @app.exception_handler(ClassificationRejected)
    async def handle_rejected(_: Request, rejected: ClassificationRejected) -> JSONResponse:
        return _error_response(422, rejected.code, rejected.message, "text")

    @app.exception_handler(ModelUnavailable)
    async def handle_model_unavailable(_: Request, unavailable: ModelUnavailable) -> JSONResponse:
        return _error_response(503, "model_unavailable", str(unavailable))

    @app.exception_handler(ClassificationFailed)
    async def handle_classification_failed(_: Request, __: ClassificationFailed) -> JSONResponse:
        return _error_response(500, "internal_error", "The message couldn't be classified. Please try again.")

    @app.exception_handler(HTTPException)
    async def handle_http_error(_: Request, error: HTTPException) -> JSONResponse:
        codes = {400: "bad_request", 404: "not_found", 405: "method_not_allowed"}
        return _error_response(error.status_code, codes.get(error.status_code, "http_error"), str(error.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, error: Exception) -> JSONResponse:
        logger.error("Unexpected error: %s", type(error).__name__)
        return _error_response(500, "internal_error", "An unexpected error occurred.")

    app.include_router(router)
    return app


app = create_app()
