# Held-Out Evaluation Runbook — Tranche 01

## Purpose

Run the frozen `heldout_tranche_01` exactly once for the current deterministic
configuration:

```text
keyword_bm25_style_v1 + deterministic_anti_anchoring_policy_v1 + top_k=5
```

The runner produces a **pass or block** result. A block is diagnostic evidence, not
a command error. Do not alter held-out cases, policy rules, ranking behavior, or
procedure eligibility while interpreting the result.

## Preconditions

- `main` contains the held-out freeze and this runner.
- The working tree is clean before the run.
- Unit tests pass.
- These report files do not already exist:

```text
evidence_vault/reports/heldout-tranche-01-keyword-policy.json
docs/reports/heldout-tranche-01-keyword-policy.md
```

If either artifact exists, preserve it. Do not delete it to rerun the same
configuration.

## Command

From the repository root:

```powershell
python .\scripts\run_heldout_evaluation.py --repository-root . --top-k 5
```

The command verifies the manifest first. A manifest mismatch exits non-zero and
writes no report. A successfully generated `blocked` report exits zero so the
baseline evidence can be committed and reviewed.

## Outputs

```text
evidence_vault/reports/heldout-tranche-01-keyword-policy.json
docs/reports/heldout-tranche-01-keyword-policy.md
```

The report includes the manifest fingerprint, repository revision when available,
configuration, case-level contract outcomes, and a strict promotion-gate status.
It excludes raw held-out intake text.

## Required interpretation

- **Passed:** only the recorded configuration passed this 12-case tranche. It still
  does not establish production readiness.
- **Blocked:** preserve the report, inspect the named case IDs and failure labels,
  then create a separate failure-autopsy/intervention slice. Do not use the held-out
  inputs to tune the implementation directly.

## Prohibited actions

- Editing held-out inputs, expected labels, or manifest hashes to make the report
  pass.
- Replacing the initial report by deleting it and rerunning the same configuration.
- Claiming semantic retrieval quality, safe remediation, customer-data validation,
  or production readiness from this run.
