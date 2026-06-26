"""Run local-SIE dense retrieval on calibration only and save comparison evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.profiles import build_local_sie_embedding_profile
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient
from incident_precedent_harness.retrieval.dense import DenseIndexError, DenseIndexStore, DenseRetriever
from incident_precedent_harness.retrieval.dense_reporting import (
    run_dense_retrieval_calibration,
    write_dense_retrieval_report,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


DEFAULT_INDEX_RELATIVE_PATH = Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
DEFAULT_JSON_REPORT = Path("evidence_vault") / "reports" / "local-sie-dense-retrieval-calibration.json"
DEFAULT_MARKDOWN_REPORT = Path("docs") / "reports" / "local-sie-dense-retrieval-calibration.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run calibration-only local-SIE dense retrieval against a validated local index."
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit local dense index path.")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")
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
                    "calibration_kind": "local_sie_dense_retrieval",
                    "status": "blocked",
                    "failure_code": "dense_index_invalid",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 1

    settings = get_settings()
    profile = build_local_sie_embedding_profile(
        timeout_ms=int(settings.sie_timeout_seconds * 1000)
    )
    client = SuperlinkedSIEClient.from_settings(settings)
    try:
        report = run_dense_retrieval_calibration(
            retriever=retriever,
            incidents=incidents,
            client=client,
            embedding_profile=profile,
            cases=cases,
            trace_id=uuid4(),
            top_k=args.top_k,
        )
    except SemanticInferenceError as error:
        print(
            json.dumps(
                {
                    "calibration_kind": "local_sie_dense_retrieval",
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

    json_report_path = root / DEFAULT_JSON_REPORT
    markdown_report_path = root / DEFAULT_MARKDOWN_REPORT
    write_dense_retrieval_report(
        report,
        json_path=json_report_path,
        markdown_path=markdown_report_path,
    )
    print(
        json.dumps(
            {
                "calibration_kind": "local_sie_dense_retrieval",
                "status": "passed",
                "calibration_case_count": report.calibration_case_count,
                "correct_precedent_mrr": report.metrics.correct_precedent_mrr,
                "incident_family_recall_at_5": report.metrics.incident_family_recall_at_5,
                "false_operational_match_rate": report.metrics.false_operational_match_rate,
                "keyword_correct_precedent_mrr": report.keyword_baseline_metrics.correct_precedent_mrr,
                "keyword_false_operational_match_rate": report.keyword_baseline_metrics.false_operational_match_rate,
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
    """Render generated evidence locations without exposing machine-specific paths."""

    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    sys.exit(main())
