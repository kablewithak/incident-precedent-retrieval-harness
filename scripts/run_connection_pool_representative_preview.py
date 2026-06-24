"""Generate calibration-only evidence for connection-pool representative preview."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from incident_precedent_harness.decisions.connection_pool_selection_preview import (
    ConnectionPoolRepresentativePreview,
    load_connection_pool_profile_set,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


REPORT_STEM = "connection-pool-representative-selection-preview-calibration"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run calibration-only connection-pool representative-selection preview. "
            "This command never loads held-out cases or changes the active policy."
        )
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")

    root = args.repository_root.resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_calibration_cases()
    profile_set = load_connection_pool_profile_set(
        root / "data" / "selection_profiles" / "connection-pool-representative-profiles.json"
    )
    preview = ConnectionPoolRepresentativePreview(
        policy=AntiAnchoringDecisionPolicy(),
        profile_set=profile_set,
    )
    retriever = KeywordRetriever(incidents)

    outcomes: list[dict[str, object]] = []
    for case in cases:
        result = preview.preview(
            intake=case,
            ranked_candidates=retriever.rank(case.input_summary, top_k=args.top_k),
            incidents=incidents,
            procedures=procedures,
        )
        if result is None:
            continue
        selected = result.retained_incident_ids
        outcomes.append(
            {
                "eval_id": case.eval_id,
                "selected_incident_ids": selected,
                "selection_status": next(
                    candidate.selection_status.value
                    for candidate in result.candidate_previews
                    if candidate.incident_id == selected[0]
                ),
                "acceptable_selection": bool(set(selected).intersection(case.acceptable_precedent_ids)),
                "unsafe_selection": bool(set(selected).intersection(case.unsafe_precedent_ids)),
                "selection_reason": result.selection_reason,
                "candidate_previews": [
                    candidate.model_dump(mode="json") for candidate in result.candidate_previews
                ],
            }
        )

    safe_selection_count = sum(
        outcome["acceptable_selection"] and not outcome["unsafe_selection"]
        for outcome in outcomes
    )
    unsafe_selection_count = sum(outcome["unsafe_selection"] for outcome in outcomes)
    payload = {
        "report_kind": "connection_pool_representative_selection_preview_calibration",
        "generated_at": datetime.now(UTC).isoformat(),
        "top_k": args.top_k,
        "active_policy_changed": False,
        "heldout_loaded": False,
        "preview_case_count": len(outcomes),
        "safe_selection_count": safe_selection_count,
        "unsafe_selection_count": unsafe_selection_count,
        "outcomes": outcomes,
        "known_limits": [
            "Calibration-only preview; no held-out case is loaded or scored.",
            "The active AntiAnchoringDecisionPolicy remains unchanged.",
            "This preview applies only to the authored connection_pool_exhaustion family.",
            "Selection uses declared profile cues after current policy compatibility; it does not use lexical rank, lexical score, incident ID, procedure ID, or evaluation labels.",
            "A passed preview does not authorize a held-out comparison or a production claim."
        ]
    }
    json_path = root / "evidence_vault" / "reports" / f"{REPORT_STEM}.json"
    markdown_path = root / "docs" / "reports" / f"{REPORT_STEM}.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(payload), encoding="utf-8")
    print(
        "Connection-pool representative-selection preview complete: "
        f"preview_cases={len(outcomes)}, safe_selections={safe_selection_count}, "
        f"unsafe_selections={unsafe_selection_count}, active_policy_changed=false"
    )
    return 0


def _markdown(payload: dict[str, object]) -> str:
    outcomes = payload["outcomes"]
    lines = [
        "# Connection-Pool Representative-Selection Preview — Calibration",
        "",
        "## Boundary",
        "",
        "This is a calibration-only preview. It does not change `AntiAnchoringDecisionPolicy`, the keyword retriever, held-out artifacts, or promotion-gate behavior.",
        "",
        "## Summary",
        "",
        f"- Preview cases: {payload['preview_case_count']}",
        f"- Safe selections: {payload['safe_selection_count']}",
        f"- Unsafe selections: {payload['unsafe_selection_count']}",
        f"- Active policy changed: {str(payload['active_policy_changed']).lower()}",
        f"- Held-out loaded: {str(payload['heldout_loaded']).lower()}",
        "",
        "## Outcomes",
        "",
        "| Case | Selected cards | Acceptable selection | Unsafe selection |",
        "|---|---|---:|---:|",
    ]
    for outcome in outcomes:
        lines.append(
            "| "
            f"{outcome['eval_id']} | {', '.join(outcome['selected_incident_ids'])} | "
            f"{str(outcome['acceptable_selection']).lower()} | "
            f"{str(outcome['unsafe_selection']).lower()} |"
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {item}" for item in payload["known_limits"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
