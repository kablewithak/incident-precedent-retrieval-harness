"""Run a controlled local SIE capability spike.

This probe validates only the local server's operation contracts:
- encode returns a non-empty dense vector;
- score returns one score per supplied candidate and valid ranks;
- extract returns an entities list.

It uses synthetic text and prints metadata-safe JSON. It does not write raw
provider payloads, claim retrieval quality, or select production profiles.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from incident_precedent_harness.domain.enums import ProviderFailureCode


DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_EXTRACTION_MODEL = "urchade/gliner_multi-v2.1"


def parse_args() -> argparse.Namespace:
    """Parse explicit capability-spike inputs."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate local SIE encode, score, and extract contracts using "
            "synthetic incident text."
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("SIE_BASE_URL", DEFAULT_BASE_URL),
        help="Local SIE base URL. Defaults to SIE_BASE_URL or localhost:8080.",
    )
    parser.add_argument(
        "--operation",
        choices=("all", "encode", "score", "extract"),
        default="all",
        help="Run all operations or one named operation.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="SIE model ID for the encode probe.",
    )
    parser.add_argument(
        "--rerank-model",
        default=DEFAULT_RERANK_MODEL,
        help="SIE model ID for the score probe.",
    )
    parser.add_argument(
        "--extraction-model",
        default=DEFAULT_EXTRACTION_MODEL,
        help="SIE model ID for the extract probe.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path for a metadata-safe JSON evidence record. Existing "
            "files are replaced only when this option is supplied explicitly."
        ),
    )
    return parser.parse_args()


def vector_dimension(value: Any) -> int:
    """Return a vector dimension without serializing vector contents."""
    shape = getattr(value, "shape", None)
    if shape is not None and len(shape) == 1:
        return int(shape[0])

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)

    raise TypeError("SIE encode response did not contain a one-dimensional vector.")


def as_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    """Validate a provider response field as a mapping."""
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping.")
    return value


def as_sequence(value: Any, field_name: str) -> Sequence[Any]:
    """Validate a provider response field as a sequence."""
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence.")
    return value


def classify_failure(error: Exception) -> tuple[ProviderFailureCode, bool, str]:
    """Classify known spike failures without emitting the raw provider message."""
    exception_type = type(error).__name__.casefold()
    message = " ".join(str(error).split()).casefold()
    combined = f"{exception_type} {message}"

    if "provision" in combined or "model load timeout" in combined:
        return (
            ProviderFailureCode.RETRY_EXHAUSTED,
            False,
            "Local SIE model did not become ready within the configured provisioning budget.",
        )
    if "503" in combined or "model not ready" in combined:
        return (
            ProviderFailureCode.MODEL_NOT_READY,
            True,
            "Local SIE model is still provisioning.",
        )
    if "timeout" in combined:
        return (
            ProviderFailureCode.PROVIDER_TIMEOUT,
            True,
            "Local SIE request exceeded its configured timeout.",
        )
    if "connection" in combined or "unavailable" in combined:
        return (
            ProviderFailureCode.PROVIDER_UNAVAILABLE,
            True,
            "Local SIE was unavailable before a validated response was received.",
        )
    return (
        ProviderFailureCode.INVALID_PROVIDER_RESPONSE,
        False,
        "Local SIE did not return a response that could be validated by the spike.",
    )


def timed_result(*, operation: str, model_id: str, run: Any) -> dict[str, Any]:
    """Execute one operation and return metadata-safe evidence."""
    started = time.perf_counter()
    try:
        metadata = run()
        return {
            "operation": operation,
            "status": "passed",
            "model_id": model_id,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            **metadata,
        }
    except Exception as error:  # Evidence capture intentionally records a safe failure class.
        code, retryable, safe_summary = classify_failure(error)
        return {
            "operation": operation,
            "status": "failed",
            "model_id": model_id,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "error_type": type(error).__name__,
            "normalized_failure_code": code.value,
            "retryable": retryable,
            "safe_failure_summary": safe_summary,
        }


def write_evidence(*, evidence: dict[str, Any], output_path: Path) -> None:
    """Write JSON only when the caller explicitly names an evidence artifact path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    """Run selected operation probes and print one JSON evidence record."""
    args = parse_args()

    try:
        from sie_sdk import SIEClient
        from sie_sdk.types import Item
    except ModuleNotFoundError:
        evidence = {
            "spike_kind": "local_sie_operation_contract",
            "status": "blocked",
            "reason": "sie_sdk_not_installed",
            "next_command": 'python -m pip install -e ".[dev,provider-spike]"',
        }
        print(json.dumps(evidence, indent=2))
        return 2

    client = SIEClient(args.base_url)
    results: list[dict[str, Any]] = []

    query_text = (
        "Synthetic RelayOps incident: queue backlog and worker rejections began "
        "immediately after a deployment."
    )

    if args.operation in {"all", "encode"}:

        def run_encode() -> dict[str, Any]:
            response = as_mapping(
                client.encode(args.embedding_model, Item(text=query_text)),
                "encode response",
            )
            dense = response.get("dense")
            dimension = vector_dimension(dense)
            if dimension <= 0:
                raise ValueError("Dense vector dimension must be greater than zero.")
            return {"dense_vector_dimension": dimension}

        results.append(
            timed_result(
                operation="encode",
                model_id=args.embedding_model,
                run=run_encode,
            )
        )

    if args.operation in {"all", "score"}:

        def run_score() -> dict[str, Any]:
            response = as_mapping(
                client.score(
                    args.rerank_model,
                    Item(text=query_text),
                    [
                        Item(
                            text=(
                                "Workers rejected messages after a schema-incompatible "
                                "deployment, and the event queue backlog grew."
                            )
                        ),
                        Item(
                            text=(
                                "Checkout latency increased because cache invalidation "
                                "failed during peak traffic."
                            )
                        ),
                    ],
                ),
                "score response",
            )
            scores = as_sequence(response.get("scores"), "scores")
            if len(scores) != 2:
                raise ValueError(f"Expected 2 score entries, received {len(scores)}.")

            ranks: list[int] = []
            for index, entry in enumerate(scores):
                score_entry = as_mapping(entry, f"scores[{index}]")
                rank = score_entry.get("rank")
                if not isinstance(rank, int):
                    raise TypeError(f"scores[{index}].rank must be an integer.")
                ranks.append(rank)

            if sorted(ranks) != [0, 1]:
                raise ValueError(f"Expected ranks [0, 1], received {ranks}.")

            return {"score_entry_count": len(scores), "returned_ranks": ranks}

        results.append(
            timed_result(
                operation="score",
                model_id=args.rerank_model,
                run=run_score,
            )
        )

    if args.operation in {"all", "extract"}:

        def run_extract() -> dict[str, Any]:
            response = as_mapping(
                client.extract(
                    args.extraction_model,
                    Item(
                        text=(
                            "Synthetic RelayOps incident: webhook-worker began rejecting "
                            "messages after a deployment. The event-queue backlog increased "
                            "and API requests returned HTTP 502 responses."
                        )
                    ),
                    labels=["service", "symptom", "change_context"],
                ),
                "extract response",
            )
            entities = as_sequence(response.get("entities"), "entities")
            returned_labels = sorted(
                {
                    str(as_mapping(entity, "entity").get("label", "unknown"))
                    for entity in entities
                }
            )
            return {"entity_count": len(entities), "returned_labels": returned_labels}

        results.append(
            timed_result(
                operation="extract",
                model_id=args.extraction_model,
                run=run_extract,
            )
        )

    evidence = {
        "spike_kind": "local_sie_operation_contract",
        "sie_base_url": args.base_url,
        "sie_sdk_version": importlib.metadata.version("sie-sdk"),
        "operation_count": len(results),
        "operations": results,
        "non_claims": [
            "Does not prove retrieval quality.",
            "Does not prove project-profile suitability.",
            "Does not prove extraction-label usefulness.",
            "Does not prove production readiness.",
        ],
    }
    if args.output:
        write_evidence(evidence=evidence, output_path=args.output)
        evidence["evidence_output"] = str(args.output)

    print(json.dumps(evidence, indent=2))
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
