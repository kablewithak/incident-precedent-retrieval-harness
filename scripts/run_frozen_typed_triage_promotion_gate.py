"""Run the frozen end-to-end typed-triage promotion gate against local SIE.

The command is intentional and writes one immutable evidence pair. A BLOCK decision
is a valid result and exits successfully after the report is created.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evaluation.heldout import HeldoutManifestIntegrityError
from incident_precedent_harness.evaluation.typed_triage_promotion import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    FrozenTypedTriageGateError,
    run_frozen_typed_triage_promotion_gate,
    write_frozen_typed_triage_promotion_report,
)
from incident_precedent_harness.inference.profiles import build_local_sie_embedding_profile
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient
from incident_precedent_harness.retrieval.dense import DenseIndexError, DenseIndexStore, DenseRetriever
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.service import (
    TriageContractError,
    TriageInputRejectedError,
    TriageService,
)

DEFAULT_INDEX_RELATIVE_PATH = (
    Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the frozen end-to-end typed-triage promotion gate. The gate verifies "
            "held-out hashes before scoring and writes one immutable report pair."
        )
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit dense-index path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    index_path = (args.index or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()

    repository = JsonDatasetRepository(root)
    try:
        incidents = repository.load_incidents()
        procedures = repository.load_procedures()
        cases = repository.load_heldout_cases()
        index = DenseIndexStore.load(index_path)
        dense_retriever = DenseRetriever(index=index, incidents=incidents)
    except (DenseIndexError, ValueError) as error:
        return _refused("candidate_setup_invalid", str(error))

    settings = get_settings()
    profile = build_local_sie_embedding_profile(
        timeout_ms=int(settings.sie_timeout_seconds * 1_000)
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
        report = run_frozen_typed_triage_promotion_gate(
            repository_root=root,
            service=service,
            incidents=incidents,
            procedures=procedures,
            cases=cases,
        )
        json_path = root / JSON_REPORT_RELATIVE_PATH
        markdown_path = root / MARKDOWN_REPORT_RELATIVE_PATH
        write_frozen_typed_triage_promotion_report(
            report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
    except HeldoutManifestIntegrityError as error:
        return _refused("heldout_freeze_verification_failed", str(error))
    except (
        FrozenTypedTriageGateError,
        TriageContractError,
        TriageInputRejectedError,
        FileExistsError,
    ) as error:
        return _refused("typed_triage_gate_refused", str(error))

    print(
        json.dumps(
            {
                "triage_kind": report.report_kind,
                "decision": report.decision.value,
                "heldout_case_count": report.metrics.heldout_case_count,
                "policy_baseline_parity_rate": report.metrics.policy_baseline_parity_rate,
                "policy_case_contract_pass_rate": report.metrics.policy_case_contract_pass_rate,
                "semantic_advisory_available_count": (
                    report.metrics.semantic_advisory_available_count
                ),
                "provider_degraded_safe_resolution_rate": (
                    report.metrics.provider_degraded_safe_resolution_rate
                ),
                "procedure_execution_authorized_count": (
                    report.metrics.procedure_execution_authorized_count
                ),
                "p50_pipeline_latency_ms": report.metrics.p50_pipeline_latency_ms,
                "p95_pipeline_latency_ms": report.metrics.p95_pipeline_latency_ms,
                "blocked_case_ids": report.metrics.blocked_case_ids,
                "evidence_json": JSON_REPORT_RELATIVE_PATH.as_posix(),
                "evidence_markdown": MARKDOWN_REPORT_RELATIVE_PATH.as_posix(),
            },
            indent=2,
        )
    )
    return 0


def _refused(failure_code: str, safe_message: str) -> int:
    print(
        json.dumps(
            {
                "triage_kind": "frozen_typed_triage_promotion_gate",
                "status": "refused",
                "failure_code": failure_code,
                "safe_message": safe_message,
            },
            indent=2,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
