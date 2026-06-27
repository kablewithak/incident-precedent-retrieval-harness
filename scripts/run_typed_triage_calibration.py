"""Run calibration-only typed triage packets with local-SIE dense advisory retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.inference.profiles import build_local_sie_embedding_profile
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient
from incident_precedent_harness.retrieval.dense import DenseIndexError, DenseIndexStore, DenseRetriever
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.reporting import (
    run_typed_triage_calibration,
    write_typed_triage_report,
)
from incident_precedent_harness.triage.service import (
    TriageContractError,
    TriageInputRejectedError,
    TriageService,
)

DEFAULT_INDEX_RELATIVE_PATH = Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
DEFAULT_JSON_REPORT = Path("evidence_vault") / "reports" / "typed-triage-calibration.json"
DEFAULT_MARKDOWN_REPORT = Path("docs") / "reports" / "typed-triage-calibration.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run calibration-only typed triage packets with advisory local-SIE dense retrieval."
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit local dense index path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    index_path = (args.index or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_calibration_cases()

    try:
        index = DenseIndexStore.load(index_path)
        dense_retriever = DenseRetriever(index=index, incidents=incidents)
    except DenseIndexError as error:
        return _blocked("dense_index_invalid", str(error))

    settings = get_settings()
    profile = build_local_sie_embedding_profile(
        timeout_ms=int(settings.sie_timeout_seconds * 1000)
    )
    service = TriageService(
        incidents=incidents,
        procedures=procedures,
        dense_retriever=dense_retriever,
        semantic_client=SuperlinkedSIEClient.from_settings(settings),
        embedding_profile=profile,
        policy=AntiAnchoringDecisionPolicy(),
    )
    try:
        report = run_typed_triage_calibration(service=service, cases=cases)
    except TriageInputRejectedError as error:
        return _blocked("triage_input_rejected", ", ".join(error.finding_codes))
    except TriageContractError as error:
        return _blocked("triage_contract_invalid", str(error))

    json_path = root / DEFAULT_JSON_REPORT
    markdown_path = root / DEFAULT_MARKDOWN_REPORT
    write_typed_triage_report(report, json_path=json_path, markdown_path=markdown_path)
    print(
        json.dumps(
            {
                "triage_kind": "typed_triage_calibration",
                "status": report.status,
                "calibration_case_count": report.calibration_case_count,
                "decision_state_match_rate": report.metrics.decision_state_match_rate,
                "semantic_advisory_available_count": report.metrics.semantic_advisory_available_count,
                "provider_degraded_packet_count": report.metrics.provider_degraded_packet_count,
                "procedure_execution_authorized_count": report.metrics.procedure_execution_authorized_count,
                "evidence_json": _repository_relative_path(root, json_path),
                "evidence_markdown": _repository_relative_path(root, markdown_path),
            },
            indent=2,
        )
    )
    return 0 if report.status == "passed" else 1


def _blocked(failure_code: str, safe_message: str) -> int:
    print(
        json.dumps(
            {
                "triage_kind": "typed_triage_calibration",
                "status": "blocked",
                "failure_code": failure_code,
                "safe_message": safe_message,
            },
            indent=2,
        )
    )
    return 1


def _repository_relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


if __name__ == "__main__":
    sys.exit(main())
