"""The API's endpoints. Model logic stays in app/ml, and error responses in app/main.py.

These are plain functions, not async ones, so FastAPI runs them in a worker thread and
model calculations can't hold up other requests.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.ml.model_info import build_model_info
from app.ml.predict import ClassificationRejected, LoadedModel, ModelUnavailable, classify
from app.ml.results import build_dataset_results, build_models_results
from app.schemas.prediction import (
    ClassifyRequest,
    ClassifyResponse,
    ErrorResponse,
    HealthResponse,
    ModelInfoResponse,
)
from app.schemas.results import DatasetResults, ModelsResults

logger = logging.getLogger("spamshield.api")

router = APIRouter(prefix="/api")


class ClassificationFailed(Exception):
    """Raised for an unexpected failure. It carries no details, so it can't expose message text."""


def _loaded_model(request: Request) -> LoadedModel:
    """Return the model loaded at startup, or raise ModelUnavailable with the reason."""
    model = request.app.state.model
    if model is None:
        raise ModelUnavailable(request.app.state.model_error)
    return model


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "The model isn't loaded."}},
)
def health(request: Request):
    """Report whether the API is running and the model is loaded."""
    model = request.app.state.model
    if model is None:
        return JSONResponse(
            status_code=503,
            content=HealthResponse(
                status="unavailable", model_loaded=False, detail=request.app.state.model_error
            ).model_dump(),
        )
    return HealthResponse(status="ok", model_loaded=True, model_version=model.metadata["model_version"])


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    responses={
        413: {"model": ErrorResponse, "description": "The request body is too large."},
        422: {"model": ErrorResponse, "description": "The text is invalid or can't be classified."},
        500: {"model": ErrorResponse, "description": "An unexpected error occurred."},
        503: {"model": ErrorResponse, "description": "The model isn't loaded."},
    },
)
def classify_email(body: ClassifyRequest, request: Request):
    """Classify one message as spam or ham, and explain the score.

    The message is not stored or logged. `confidence` is always null, because a Linear
    SVM doesn't provide a meaningful probability.
    """
    model = _loaded_model(request)
    try:
        result = classify(model, body.text)
    except ClassificationRejected:
        raise
    except Exception as error:
        # Only the error's type is logged, because its message could include the text.
        logger.error("Classification failed: %s", type(error).__name__)
        raise ClassificationFailed from None
    return ClassifyResponse(
        model_version=model.metadata["model_version"],
        text_length=len(body.text),
        **result,
    )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    responses={503: {"model": ErrorResponse, "description": "The model isn't loaded."}},
)
def model_info(request: Request):
    """Describe the model, its measured results, and its limitations."""
    return build_model_info(_loaded_model(request))


@router.get(
    "/results/models",
    response_model=ModelsResults,
    responses={503: {"model": ErrorResponse, "description": "A saved report can't be read."}},
)
def models_results():
    """Return the saved model comparison, final evaluation and source-leakage results.

    This only reads committed reports, so it works without the model being loaded.
    """
    return build_models_results()


@router.get(
    "/results/dataset",
    response_model=DatasetResults,
    responses={503: {"model": ErrorResponse, "description": "A saved report can't be read."}},
)
def dataset_results():
    """Return verified aggregate statistics about the dataset. It includes no email text."""
    return build_dataset_results()
