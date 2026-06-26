"""Local Superlinked SIE adapter for the structured-first submission path.

Only this module imports or handles SIE SDK response shapes. It exposes the
provider-neutral semantic inference contract used by the rest of the harness.
The initial submission path supports local Docker ``encode`` and ``score`` only.
``extract`` is intentionally fail-closed until a separately validated profile exists.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, TypeVar

from incident_precedent_harness.config.settings import Settings, get_settings
from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.failure_normalization import (
    normalize_local_sie_failure,
)
from incident_precedent_harness.inference.models import (
    CandidateScore,
    CandidateScoringRequest,
    CandidateScoringResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EncodedVector,
    IncidentExtractionRequest,
    IncidentExtractionResponse,
    ProviderFailure,
)


class _SIEClientLike(Protocol):
    """Narrow SDK shape used by this adapter and deterministic tests."""

    def encode(self, model_id: str, item: object) -> object:
        """Encode one text item."""

    def score(self, model_id: str, query: object, candidates: list[object]) -> object:
        """Score a query against ordered candidate items."""


T = TypeVar("T")


class _AdapterUnavailableError(RuntimeError):
    """Internal initialization failure carrying no provider payload."""

    def __init__(self, code: ProviderFailureCode, safe_message: str) -> None:
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message


class SuperlinkedSIEClient:
    """Provider-neutral client backed by a local Docker SIE instance.

    Provider objects, response mappings, and provider exception messages remain
    confined to this class. The public methods return typed application models or
    raise ``SemanticInferenceError`` carrying only a safe failure envelope.
    """

    def __init__(
        self,
        *,
        client: _SIEClientLike | None,
        item_factory: Callable[..., object] | None,
        initialization_failure: ProviderFailureCode | None = None,
        initialization_message: str | None = None,
        retry_delay_seconds: float = 0.05,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")
        self._client = client
        self._item_factory = item_factory
        self._initialization_failure = initialization_failure
        self._initialization_message = initialization_message
        self._retry_delay_seconds = retry_delay_seconds
        self._sleeper = sleeper

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "SuperlinkedSIEClient":
        """Build a local-only SDK client without exposing settings or secrets."""
        active_settings = settings or get_settings()
        if not active_settings.is_local_sie:
            return cls(
                client=None,
                item_factory=None,
                initialization_failure=ProviderFailureCode.UNSUPPORTED_CAPABILITY,
                initialization_message=(
                    "Managed SIE endpoints are not enabled for the local submission path."
                ),
            )

        try:
            from sie_sdk import SIEClient
            from sie_sdk.types import Item
        except ModuleNotFoundError:
            return cls(
                client=None,
                item_factory=None,
                initialization_failure=ProviderFailureCode.UNSUPPORTED_CAPABILITY,
                initialization_message="The local SIE SDK dependency is not installed.",
            )

        return cls(client=SIEClient(active_settings.sie_base_url), item_factory=Item)

    def extract_incident_signals(
        self,
        request: IncidentExtractionRequest,
    ) -> IncidentExtractionResponse:
        """Fail closed because local extraction is not part of the approved path."""
        raise SemanticInferenceError(
            ProviderFailure(
                trace_id=request.trace_id,
                profile_id=request.profile.profile_id,
                operation=ProviderOperation.EXTRACT,
                code=ProviderFailureCode.UNSUPPORTED_CAPABILITY,
                safe_message=(
                    "Local SIE extraction is not enabled for the structured-first "
                    "submission path."
                ),
                retryable=False,
            )
        )

    def encode_incident_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Encode sanitized items and validate vectors before they enter the harness."""
        vectors, latency_ms = self._execute(
            request=request,
            operation=ProviderOperation.ENCODE,
            run=lambda: self._encode_all(request),
        )
        return EmbeddingResponse(
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
            vectors=vectors,
            latency_ms=latency_ms,
        )

    def score_incident_candidates(
        self,
        request: CandidateScoringRequest,
    ) -> CandidateScoringResponse:
        """Score ordered candidates and return a typed rank order.

        The local SDK returns score entries in input-candidate order, each with a
        zero-based ``rank``. The adapter binds each entry to the candidate at the
        same input position and converts ranks to the one-based application contract.
        The manual provider validation script rechecks this contract using a
        deliberately discriminative synthetic pair.
        """
        scores, latency_ms = self._execute(
            request=request,
            operation=ProviderOperation.SCORE,
            run=lambda: self._parse_scores(
                response=self._as_mapping(
                    self._require_client().score(
                        request.profile.model_id,
                        self._require_item_factory()(text=request.query.text),
                        [self._require_item_factory()(text=candidate.text) for candidate in request.candidates],
                    ),
                    field_name="score response",
                ),
                candidate_ids=tuple(candidate.item_id for candidate in request.candidates),
            ),
        )
        return CandidateScoringResponse(
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
            scores=scores,
            latency_ms=latency_ms,
        )

    def _execute(
        self,
        *,
        request: EmbeddingRequest | CandidateScoringRequest,
        operation: ProviderOperation,
        run: Callable[[], T],
    ) -> tuple[T, int]:
        started = time.perf_counter()
        attempt_count = request.profile.max_retries + 1
        for attempt in range(attempt_count):
            try:
                return run(), round((time.perf_counter() - started) * 1000)
            except SemanticInferenceError:
                raise
            except _AdapterUnavailableError as error:
                raise SemanticInferenceError(
                    ProviderFailure(
                        trace_id=request.trace_id,
                        profile_id=request.profile.profile_id,
                        operation=operation,
                        code=error.code,
                        safe_message=error.safe_message,
                        retryable=False,
                    )
                ) from None
            except (TypeError, ValueError):
                raise SemanticInferenceError(
                    ProviderFailure(
                        trace_id=request.trace_id,
                        profile_id=request.profile.profile_id,
                        operation=operation,
                        code=ProviderFailureCode.INVALID_PROVIDER_RESPONSE,
                        safe_message="Local SIE returned a response that could not be validated.",
                        retryable=False,
                    )
                ) from None
            except Exception as error:
                exhausted = attempt == attempt_count - 1
                failure = normalize_local_sie_failure(
                    trace_id=request.trace_id,
                    profile_id=request.profile.profile_id,
                    operation=operation,
                    exception_type=type(error).__name__,
                    message=str(error),
                    retries_exhausted=exhausted,
                )
                if exhausted or not failure.retryable:
                    raise SemanticInferenceError(failure) from None
                self._sleeper(self._retry_delay_seconds * (2**attempt))
        raise AssertionError("bounded provider retry loop exited unexpectedly")

    def _encode_all(self, request: EmbeddingRequest) -> tuple[EncodedVector, ...]:
        client = self._require_client()
        item_factory = self._require_item_factory()
        vectors = tuple(
            EncodedVector(
                item_id=item.item_id,
                dense_values=self._parse_dense_vector(
                    self._as_mapping(
                        client.encode(request.profile.model_id, item_factory(text=item.text)),
                        field_name="encode response",
                    ).get("dense"),
                ),
            )
            for item in request.items
        )
        self._validate_consistent_dimensions(vectors)
        return vectors

    def _require_client(self) -> _SIEClientLike:
        if self._client is not None:
            return self._client
        raise _AdapterUnavailableError(
            self._initialization_failure or ProviderFailureCode.UNSUPPORTED_CAPABILITY,
            self._initialization_message or "Local SIE client is unavailable.",
        )

    def _require_item_factory(self) -> Callable[..., object]:
        if self._item_factory is not None:
            return self._item_factory
        raise _AdapterUnavailableError(
            self._initialization_failure or ProviderFailureCode.UNSUPPORTED_CAPABILITY,
            self._initialization_message or "Local SIE item factory is unavailable.",
        )

    @staticmethod
    def _as_mapping(value: object, *, field_name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping.")
        return value

    @staticmethod
    def _parse_dense_vector(value: object) -> tuple[float, ...]:
        """Accept SDK array-like vectors without leaking provider-specific types.

        The local SIE SDK may return a NumPy-style object rather than a Python
        ``Sequence``. ``tolist`` is the narrow, provider-agnostic normalization
        seam: it accepts one-dimensional array-like vectors while the remaining
        validation still rejects strings, mappings, empty vectors, nested values,
        non-numeric values, and non-finite values.
        """
        if isinstance(value, (str, bytes, bytearray)):
            raise ValueError("encode response dense field must be a sequence.")

        normalized_value: object = value
        if not isinstance(normalized_value, Sequence):
            tolist = getattr(normalized_value, "tolist", None)
            if not callable(tolist):
                raise ValueError("encode response dense field must be a sequence.")
            normalized_value = tolist()

        if (
            isinstance(normalized_value, (str, bytes, bytearray))
            or not isinstance(normalized_value, Sequence)
        ):
            raise ValueError("encode response dense field must be a sequence.")

        dense_values = tuple(float(item) for item in normalized_value)
        if not dense_values or not all(math.isfinite(item) for item in dense_values):
            raise ValueError("encode response dense field must contain finite values.")
        return dense_values

    @staticmethod
    def _validate_consistent_dimensions(vectors: tuple[EncodedVector, ...]) -> None:
        dimensions = {len(vector.dense_values) for vector in vectors}
        if len(dimensions) != 1:
            raise ValueError("encode response vectors have inconsistent dimensions.")

    @classmethod
    def _parse_scores(
        cls,
        *,
        response: Mapping[str, Any],
        candidate_ids: tuple[str, ...],
    ) -> tuple[CandidateScore, ...]:
        raw_scores = response.get("scores")
        if isinstance(raw_scores, (str, bytes, bytearray)) or not isinstance(raw_scores, Sequence):
            raise ValueError("score response scores field must be a sequence.")
        if len(raw_scores) != len(candidate_ids):
            raise ValueError("score response count must match requested candidate count.")

        parsed: list[CandidateScore] = []
        seen_ranks: set[int] = set()
        for position, raw_entry in enumerate(raw_scores):
            entry = cls._as_mapping(raw_entry, field_name=f"scores[{position}]")
            raw_rank = entry.get("rank")
            raw_score = entry.get("score")
            if isinstance(raw_rank, bool) or not isinstance(raw_rank, int):
                raise ValueError(f"scores[{position}].rank must be an integer.")
            if raw_rank < 0 or raw_rank >= len(candidate_ids) or raw_rank in seen_ranks:
                raise ValueError("score response ranks must be unique and contiguous.")
            if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
                raise ValueError(f"scores[{position}].score must be numeric.")
            score = float(raw_score)
            # Local SIE cross-encoder scores are provider-native raw relevance
            # values, not calibrated probabilities. Negative values and values
            # above one are valid; rank determines display ordering.
            if not math.isfinite(score):
                raise ValueError("score response scores must be finite raw relevance values.")
            seen_ranks.add(raw_rank)
            parsed.append(
                CandidateScore(
                    candidate_id=candidate_ids[position],
                    rank=raw_rank + 1,
                    score=score,
                )
            )

        if seen_ranks != set(range(len(candidate_ids))):
            raise ValueError("score response ranks must cover every candidate exactly once.")
        return tuple(sorted(parsed, key=lambda item: item.rank))
