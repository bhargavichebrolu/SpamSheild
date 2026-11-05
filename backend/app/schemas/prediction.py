"""Request and response shapes for the API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from app.config import MAX_INPUT_CHARS


class ClassifyRequest(BaseModel):
    text: str = Field(
        max_length=MAX_INPUT_CHARS,
        description=f"The email text to classify, up to {MAX_INPUT_CHARS:,} characters.",
        examples=["Congratulations! You have won a prize. Click here to claim."],
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise PydanticCustomError("text_empty", "The text is empty.")
        return value


class TermContribution(BaseModel):
    term: str = Field(description="A term from the message, as the model sees it.")
    contribution: float = Field(description="This term's part in the score. Positive leans towards spam.")


class Explanation(BaseModel):
    spam_terms: list[TermContribution] = Field(description="Terms pushing the score most towards spam.")
    ham_terms: list[TermContribution] = Field(description="Terms pushing the score most towards ham.")
    other_terms_total: float = Field(description="The combined contribution of all terms not listed.")
    intercept: float = Field(description="The model's starting score, before any terms.")
    note: str


class ClassifyResponse(BaseModel):
    label: Literal["spam", "ham"]
    confidence: None = Field(
        default=None,
        description="Always null. A Linear SVM doesn't provide a meaningful probability.",
    )
    score: float = Field(description="The model's raw score. It isn't a probability. See /api/model-info.")
    model_version: str
    text_length: int = Field(description="The number of characters received.")
    terms_recognised: int = Field(description="How many different terms were found in the model's vocabulary.")
    explanation: Explanation


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    model_loaded: bool
    model_version: str | None = None
    detail: str | None = None


class NoCloseMatchResults(BaseModel):
    rows: int
    f1_spam: float


class TestResults(BaseModel):
    split: str
    rows: int
    accuracy: float
    precision_spam: float
    recall_spam: float
    f1_spam: float
    roc_auc: float
    ham_flagged_as_spam: int
    spam_missed: int
    no_close_training_match: NoCloseMatchResults
    report_matches_loaded_file: bool


class StyleShiftResults(BaseModel):
    f1_without_word_removal: float
    f1_with_word_removal: float


class CrossStyleResults(BaseModel):
    note: str
    digit_style_to_placeholder_style: StyleShiftResults
    placeholder_style_to_digit_style: StyleShiftResults


class ModelInfoResponse(BaseModel):
    model_version: str
    model_type: str
    setting: dict[str, float]
    features: str
    vocabulary_size: int
    removed_word_count: int
    training_rows: int
    max_input_characters: int
    provides_probability: bool
    score_meaning: str
    file_sha256: str
    model_content_sha256: str
    test_results: TestResults | None
    cross_style_results: CrossStyleResults | None
    limitations: list[str]


class ErrorDetail(BaseModel):
    code: str = Field(description="A stable code that code can check.")
    message: str = Field(description="A message suitable for showing to a person.")
    field: str | None = Field(default=None, description="The request field involved, if any.")


class ErrorResponse(BaseModel):
    error: ErrorDetail
