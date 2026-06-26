"""Run E1 policy-shadow integration calibration without held-out assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.decisions.models import PolicyShadowRequest
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evals.shadow_integration import (
    load_shadow_integration_calibration_cases,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import KeywordCandidate
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run trace-only policy shadow integration calibration."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing calibration-only data and source code.",
    )
    return parser.parse_args()


def _ranked(retriever: KeywordRetriever, summary: str) -> tuple[KeywordCandidate, ...]:
    return retriever.rank(summary, top_k=5)


def _trace_projection(trace) -> dict[str, object]:
    return {
        "incident_family": trace.incident_family.value,
        "admitted_candidate_ids": list(trace.admitted_candidate_ids),
        "selection_intake_present": trace.selection_intake_present,
        "selector_invoked": trace.selector_invoked,
        "selection_state": trace.selection_state.value,
        "representative_incident_ids": list(trace.representative_incident_ids),
        "unavailable_reason": trace.unavailable_reason,
    }


def _expected_projection(expected) -> dict[str, object]:
    return {
        "incident_family": expected.incident_family.value,
        "admitted_candidate_ids": list(expected.admitted_candidate_ids),
        "selection_intake_present": expected.selection_intake_present,
        "selector_invoked": expected.selector_invoked,
        "selection_state": expected.selection_state.value,
        "representative_incident_ids": list(expected.representative_incident_ids),
        "unavailable_reason": expected.unavailable_reason,
    }


def _reverse_ranked_candidates(
    candidates: tuple[KeywordCandidate, ...],
) -> tuple[KeywordCandidate, ...]:
    return tuple(
        KeywordCandidate(
            incident_id=candidate.incident_id,
            rank=index,
            score=candidate.score,
            matched_terms=candidate.matched_terms,
        )
        for index, candidate in enumerate(reversed(candidates), start=1)
    )


def _changed_public_fields(left, right) -> list[str]:
    left_payload = left.model_dump(mode="json")
    right_payload = right.model_dump(mode="json")
    return sorted(
        field
        for field in left_payload
        if left_payload[field] != right_payload[field]
    )


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    policy_cases = {case.eval_id: case for case in repository.load_calibration_cases()}
    shadow_cases = load_shadow_integration_calibration_cases(root)
    retriever = KeywordRetriever(incidents)
    policy = AntiAnchoringDecisionPolicy()

    invariance_failures: list[str] = []
    for policy_case in policy_cases.values():
        ranked = _ranked(retriever, policy_case.input_summary)
        active = policy.evaluate(
            intake=policy_case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
        )
        shadow = policy.evaluate_with_shadow(
            intake=policy_case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
            shadow_request=PolicyShadowRequest(),
        )
        if shadow.policy_result != active:
            invariance_failures.append(str(policy_case.eval_id))

    fixture_failures: list[str] = []
    fixture_results: list[dict[str, object]] = []
    for fixture in shadow_cases:
        policy_case = policy_cases.get(fixture.policy_case_id)
        if policy_case is None:
            fixture_failures.append(f"{fixture.shadow_case_id}: unknown policy case")
            continue
        ranked = _ranked(retriever, policy_case.input_summary)
        active = policy.evaluate(
            intake=policy_case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
        )
        shadow = policy.evaluate_with_shadow(
            intake=policy_case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
            shadow_request=PolicyShadowRequest(
                selection_intake_bindings=fixture.selection_intake_bindings
            ),
        )
        traces_match = [_trace_projection(trace) for trace in shadow.selection_traces] == [
            _expected_projection(expected) for expected in fixture.expected_traces
        ]
        public_matches = shadow.policy_result == active
        if not traces_match or not public_matches:
            fixture_failures.append(str(fixture.shadow_case_id))
        fixture_results.append(
            {
                "shadow_case_id": fixture.shadow_case_id,
                "policy_case_id": fixture.policy_case_id,
                "public_result_invariant": public_matches,
                "trace_contract_matched": traces_match,
            }
        )

    order_fixture = next(
        fixture for fixture in shadow_cases if fixture.shadow_case_id == "SHADOW-CAL-005"
    )
    order_policy_case = policy_cases[order_fixture.policy_case_id]
    canonical_ranked = _ranked(retriever, order_policy_case.input_summary)
    reversed_ranked = _reverse_ranked_candidates(canonical_ranked)
    request = PolicyShadowRequest(
        selection_intake_bindings=order_fixture.selection_intake_bindings
    )
    canonical_active = policy.evaluate(
        intake=order_policy_case,
        ranked_candidates=canonical_ranked,
        incidents=incidents,
        procedures=procedures,
    )
    canonical_shadow = policy.evaluate_with_shadow(
        intake=order_policy_case,
        ranked_candidates=canonical_ranked,
        incidents=incidents,
        procedures=procedures,
        shadow_request=request,
    )
    reversed_active = policy.evaluate(
        intake=order_policy_case,
        ranked_candidates=reversed_ranked,
        incidents=incidents,
        procedures=procedures,
    )
    reversed_shadow = policy.evaluate_with_shadow(
        intake=order_policy_case,
        ranked_candidates=reversed_ranked,
        incidents=incidents,
        procedures=procedures,
        shadow_request=request,
    )
    order_trace_invariant = canonical_shadow.selection_traces == reversed_shadow.selection_traces
    per_input_invariant = (
        canonical_shadow.policy_result == canonical_active
        and reversed_shadow.policy_result == reversed_active
    )
    changed_fields = _changed_public_fields(canonical_active, reversed_active)

    passed = not invariance_failures and not fixture_failures and order_trace_invariant and per_input_invariant
    report = {
        "report_kind": "policy_shadow_integration_calibration",
        "shadow_integration_cases": len(shadow_cases),
        "existing_policy_calibration_cases": len(policy_cases),
        "public_result_invariance_failures": invariance_failures,
        "fixture_failures": fixture_failures,
        "order_trace_invariant": order_trace_invariant,
        "same_input_policy_invariant": per_input_invariant,
        "legacy_rank_sensitivity_observation": {
            "policy_case_id": "EVAL-009",
            "changed_public_fields": changed_fields,
            "observed": bool(changed_fields),
        },
        "active_policy_changed": False,
        "heldout_loaded": False,
        "freeze_manifest_loaded": False,
        "baseline_comparison_loaded": False,
        "promotion_report_loaded": False,
        "selector_activation_claim": False,
        "status": "PASS" if passed else "FAIL",
        "fixture_results": fixture_results,
    }

    markdown_lines = [
        "# Policy Shadow Integration Calibration",
        "",
        f"- Shadow integration fixtures: {len(shadow_cases)}",
        f"- Existing policy calibration cases checked for same-input public invariance: {len(policy_cases)}",
        f"- Public-result invariance failures: {len(invariance_failures)}",
        f"- Bridge-fixture failures: {len(fixture_failures)}",
        f"- Shadow trace order invariant: `{str(order_trace_invariant).lower()}`",
        f"- Same-input policy invariant: `{str(per_input_invariant).lower()}`",
        f"- Legacy rank-sensitivity observation: `{str(bool(changed_fields)).lower()}`",
        f"- Changed public fields under EVAL-009 rank reversal: {', '.join(changed_fields) or 'none'}",
        "- Active policy changed: `false`",
        "- Held-out loaded: `false`",
        "- Selector activation claim: `false`",
        f"- Status: **{report['status']}**",
        "",
        "The shadow trace is non-authoritative. It does not replace retained precedent IDs, decision state, missing-fact aggregation, or procedure eligibility.",
    ]
    json_path = root / "evidence_vault" / "reports" / "policy-shadow-integration-calibration.json"
    markdown_path = root / "docs" / "reports" / "policy-shadow-integration-calibration.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    print("POLICY SHADOW INTEGRATION CALIBRATION")
    print("-------------------------------------")
    print(f"shadow_integration_cases={len(shadow_cases)}")
    print(f"existing_policy_calibration_cases={len(policy_cases)}")
    print(f"public_result_invariance_failures={len(invariance_failures)}")
    print(f"fixture_failures={len(fixture_failures)}")
    print(f"shadow_trace_order_invariant={str(order_trace_invariant).lower()}")
    print(f"legacy_rank_sensitivity_observed={str(bool(changed_fields)).lower()}")
    print("active_policy_changed=false")
    print("heldout_loaded=false")
    print("freeze_manifest_loaded=false")
    print("baseline_comparison_loaded=false")
    print("promotion_report_loaded=false")
    print("selector_activation_claim=false")
    print(f"status={report['status']}")
    print(f"markdown_report={markdown_path}")
    print(f"machine_report={json_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
