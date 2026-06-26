"""Run bounded SIE score reranking over local dense top-k calibration candidates."""

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
from incident_precedent_harness.retrieval.rerank import DenseRerankError
from incident_precedent_harness.retrieval.rerank_reporting import (
    run_dense_rerank_calibration,
    write_dense_rerank_report,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


DEFAULT_INDEX_RELATIVE_PATH = Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
DEFAULT_JSON_REPORT = Path("evidence_vault") / "reports" / "local-sie-dense-rerank-calibration.json"
DEFAULT_MARKDOWN_REPORT = Path("docs") / "reports" / "local-sie-dense-rerank-calibration.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run calibration-only local-SIE score reranking over dense top-k candidates."
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit local dense index path.")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1 or args.top_k > 10:
        raise SystemExit("--top-k must be between 1 and 10 for bounded score reranking")
    root = args.repository_root.resolve()
    index_path = (args.index or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    cases = repository.load_calibration_cases()

    try:
        index = DenseIndexStore.load(index_path)
        retriever = DenseRetriever(index=index, incidents=incidents)
    except DenseIndexError as error:
        print(
            json.dumps(
                {
                    "calibration_kind": "local_sie_dense_rerank",
                    "status": "blocked",
                    "failure_code": "dense_index_invalid",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 1

    settings = get_settings()
    timeout_ms = int(settings.sie_timeout_seconds * 1000)
    embedding_profile = build_local_sie_embedding_profile(timeout_ms=timeout_ms)
    score_profile = build_local_sie_rerank_profile(timeout_ms=timeout_ms)
    client = SuperlinkedSIEClient.from_settings(settings)
    try:
        report = run_dense_rerank_calibration(
            retriever=retriever,
            incidents=incidents,
            client=client,
            embedding_profile=embedding_profile,
            score_profile=score_profile,
            cases=cases,
            trace_id=uuid4(),
            top_k=args.top_k,
        )
    except SemanticInferenceError as error:
        print(
            json.dumps(
                {
                    "calibration_kind": "local_sie_dense_rerank",
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
    except DenseRerankError as error:
        print(
            json.dumps(
                {
                    "calibration_kind": "local_sie_dense_rerank",
                    "status": "blocked",
                    "failure_code": "rerank_contract_invalid",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 1

    json_report_path = root / DEFAULT_JSON_REPORT
    markdown_report_path = root / DEFAULT_MARKDOWN_REPORT
    write_dense_rerank_report(
        report,
        json_path=json_report_path,
        markdown_path=markdown_report_path,
    )
    print(
        json.dumps(
            {
                "calibration_kind": "local_sie_dense_rerank",
                "status": "passed",
                "calibration_case_count": report.calibration_case_count,
                "dense_top_k": report.dense_top_k,
                "keyword_correct_precedent_mrr": report.keyword_baseline_metrics.correct_precedent_mrr,
                "dense_correct_precedent_mrr": report.dense_metrics.correct_precedent_mrr,
                "reranked_correct_precedent_mrr": report.rerank_metrics.correct_precedent_mrr,
                "keyword_false_operational_match_rate": report.keyword_baseline_metrics.false_operational_match_rate,
                "dense_false_operational_match_rate": report.dense_metrics.false_operational_match_rate,
                "reranked_false_operational_match_rate": report.rerank_metrics.false_operational_match_rate,
                "index_id": report.index_manifest.index_id,
                "corpus_fingerprint_sha256": report.index_manifest.corpus_fingerprint_sha256,
                "evidence_json": _repository_relative_path(root, json_report_path),
                "evidence_markdown": _repository_relative_path(root, markdown_report_path),
            },
            indent=2,
        )
    )
    return 0


def _repository_relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    sys.exit(main())
