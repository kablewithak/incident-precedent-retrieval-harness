"""Manually validate the local SIE operations used by the submission path.

This command uses synthetic RelayOps text and emits metadata-safe evidence only.
It is intentionally excluded from the ordinary deterministic unit suite.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.models import CandidateScoringRequest, EmbeddingRequest, TextItem
from incident_precedent_harness.inference.profiles import (
    build_local_sie_embedding_profile,
    build_local_sie_rerank_profile,
)
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local SIE encode and score for the submission path."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional explicit path for a metadata-safe JSON evidence record.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    timeout_ms = int(settings.sie_timeout_seconds * 1000)
    embedding_profile = build_local_sie_embedding_profile(timeout_ms=timeout_ms)
    rerank_profile = build_local_sie_rerank_profile(timeout_ms=timeout_ms)
    client = SuperlinkedSIEClient.from_settings(settings)
    trace_id = uuid4()
    query = TextItem(
        item_id="TRIAGE-SYNTHETIC-001",
        text=(
            "Synthetic RelayOps incident: queue backlog and worker rejections began "
            "immediately after a deployment."
        ),
    )
    candidates = (
        TextItem(
            item_id="INC-SIE-001",
            text=(
                "Synthetic RelayOps precedent: worker deployment introduced schema "
                "incompatibility, consumers rejected messages, and queue backlog grew."
            ),
        ),
        TextItem(
            item_id="INC-SIE-002",
            text=(
                "Synthetic RelayOps precedent: cache invalidation failed during peak "
                "traffic and checkout latency increased."
            ),
        ),
    )

    try:
        embedding_response = client.encode_incident_texts(
            EmbeddingRequest(
                trace_id=trace_id,
                profile=embedding_profile,
                items=(query, *candidates),
            )
        )
        score_response = client.score_incident_candidates(
            CandidateScoringRequest(
                trace_id=trace_id,
                profile=rerank_profile,
                query=query,
                candidates=candidates,
            )
        )
    except SemanticInferenceError as error:
        evidence = {
            "validation_kind": "local_sie_submission_operations",
            "status": "blocked",
            "trace_id": str(error.failure.trace_id),
            "profile_id": error.failure.profile_id,
            "operation": error.failure.operation.value,
            "failure_code": error.failure.code.value,
            "retryable": error.failure.retryable,
            "safe_message": error.failure.safe_message,
        }
        print(json.dumps(evidence, indent=2))
        return 1

    dimensions = {len(vector.dense_values) for vector in embedding_response.vectors}
    ranked_candidate_ids = [score.candidate_id for score in score_response.scores]
    mapping_contract_pass = ranked_candidate_ids == ["INC-SIE-001", "INC-SIE-002"]
    evidence = {
        "validation_kind": "local_sie_submission_operations",
        "status": "passed" if mapping_contract_pass else "failed",
        "trace_id": str(trace_id),
        "provider_mode": "local_docker_sie",
        "encode": {
            "profile_id": embedding_response.profile_id,
            "vector_count": len(embedding_response.vectors),
            "vector_dimension": next(iter(dimensions)),
            "latency_ms": embedding_response.latency_ms,
        },
        "score": {
            "profile_id": score_response.profile_id,
            "candidate_count": len(score_response.scores),
            "ranked_candidate_ids": ranked_candidate_ids,
            "mapping_contract_pass": mapping_contract_pass,
            "latency_ms": score_response.latency_ms,
        },
        "non_claims": [
            "Does not prove retrieval quality.",
            "Does not prove safe operational comparability.",
            "Does not prove warm-operation latency.",
            "Does not prove hosted-provider access or production readiness.",
        ],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        evidence["evidence_output"] = str(args.output)
    print(json.dumps(evidence, indent=2))
    return 0 if mapping_contract_pass else 1


if __name__ == "__main__":
    sys.exit(main())
