"""Run bounded keyword-plus-dense SIE score reranking on calibration fixtures only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.profiles import (
    build_local_sie_embedding_profile,
    build_local_sie_rerank_profile,
)
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient
from incident_precedent_harness.retrieval.dense import DenseIndexError, DenseIndexStore, DenseRetriever
from incident_precedent_harness.retrieval.hybrid import HybridCandidatePoolError
from incident_precedent_harness.retrieval.hybrid_reporting import (
    run_hybrid_rerank_calibration,
    write_hybrid_rerank_report,
)
from incident_precedent_harness.retrieval.rerank import DenseRerankError
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository

DEFAULT_INDEX_RELATIVE_PATH = Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
DEFAULT_JSON_REPORT = Path("evidence_vault") / "reports" / "local-sie-hybrid-rerank-calibration.json"
DEFAULT_MARKDOWN_REPORT = Path("docs") / "reports" / "local-sie-hybrid-rerank-calibration.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run bounded keyword-plus-dense SIE score reranking on calibration only."
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit local dense index path.")
    parser.add_argument("--keyword-top-k", type=int, default=5)
    parser.add_argument("--dense-top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.keyword_top_k < 1 or args.keyword_top_k > 5:
        raise SystemExit("--keyword-top-k must be between 1 and 5")
    if args.dense_top_k < 1 or args.dense_top_k > 5:
        raise SystemExit("--dense-top-k must be between 1 and 5")

    root = args.repository_root.resolve()
    index_path = (args.index or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    cases = repository.load_calibration_cases()

    try:
        index = DenseIndexStore.load(index_path)
        retriever = DenseRetriever(index=index, incidents=incidents)
    except DenseIndexError as error:
        _write_blocked("dense_index_invalid", str(error))
        return 1

    settings = get_settings()
    timeout_ms = int(settings.sie_timeout_seconds * 1000)
    embedding_profile = build_local_sie_embedding_profile(timeout_ms=timeout_ms)
    score_profile = build_local_sie_rerank_profile(timeout_ms=timeout_ms)
    client = SuperlinkedSIEClient.from_settings(settings)

    try:
        report = run_hybrid_rerank_calibration(
            retriever=retriever,
            incidents=incidents,
            client=client,
            embedding_profile=embedding_profile,
            score_profile=score_profile,
            cases=cases,
            trace_id=uuid4(),
            keyword_top_k=args.keyword_top_k,
            dense_top_k=args.dense_top_k,
        )
    except SemanticInferenceError as error:
        print(
            json.dumps(
                {
                    "calibration_kind": "local_sie_hybrid_rerank",
                    "status": "blocked",
                    "profile_id": error.failure.profile_id,
                    "operation": error.failure.operation.value,
                    "failure_code": error.failure.code.value,
                    "retryable": error.failure.retryable,
                    "safe_message": error.failure.safe_message,
                },
                indent=2,
            )
        )
        return 1
    except (DenseRerankError, HybridCandidatePoolError, ValueError) as error:
        _write_blocked("hybrid_rerank_contract_invalid", str(error))
        return 1

    json_report_path = root / DEFAULT_JSON_REPORT
    markdown_report_path = root / DEFAULT_MARKDOWN_REPORT
    write_hybrid_rerank_report(
        report,
        json_path=json_report_path,
        markdown_path=markdown_report_path,
    )
    comparison = report.comparison
    print(
        json.dumps(
            {
                "calibration_kind": "local_sie_hybrid_rerank",
                "status": "passed",
                "calibration_case_count": report.calibration_case_count,
                "keyword_top_k": report.keyword_top_k,
                "dense_top_k": report.dense_top_k,
                "hybrid_max_candidates": report.hybrid_max_candidates,
                "evaluation_top_k": report.evaluation_top_k,
                "keyword_correct_precedent_mrr": comparison.keyword_correct_precedent_mrr,
                "dense_correct_precedent_mrr": comparison.dense_correct_precedent_mrr,
                "dense_reranked_correct_precedent_mrr": (
                    comparison.dense_reranked_correct_precedent_mrr
                ),
                "hybrid_reranked_correct_precedent_mrr": (
                    comparison.hybrid_reranked_correct_precedent_mrr
                ),
                "keyword_false_operational_match_rate": (
                    comparison.keyword_false_operational_match_rate
                ),
                "dense_false_operational_match_rate": (
                    comparison.dense_false_operational_match_rate
                ),
                "dense_reranked_false_operational_match_rate": (
                    comparison.dense_reranked_false_operational_match_rate
                ),
                "hybrid_reranked_false_operational_match_rate": (
                    comparison.hybrid_reranked_false_operational_match_rate
                ),
                "evidence_json": _repository_relative_path(root, json_report_path),
                "evidence_markdown": _repository_relative_path(root, markdown_report_path),
            },
            indent=2,
        )
    )
    return 0


def _write_blocked(failure_code: str, safe_message: str) -> None:
    print(
        json.dumps(
            {
                "calibration_kind": "local_sie_hybrid_rerank",
                "status": "blocked",
                "failure_code": failure_code,
                "safe_message": safe_message,
            },
            indent=2,
        )
    )


def _repository_relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    sys.exit(main())
