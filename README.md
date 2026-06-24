# Phase 1.1 — Dataset Constitution & Schema Slice

Copy the contents of this ZIP into the repository root while on the branch:

```text
data/phase-1-dataset-constitution
```

It establishes source-grounded synthetic data contracts only. It does not
author the 32-card incident corpus, create a held-out set, or claim a retrieval
baseline.

Files included:

- `src/incident_precedent_harness/domain/incident_enums.py`
- `src/incident_precedent_harness/domain/incident_data.py`
- `src/incident_precedent_harness/domain/__init__.py`
- `tests/unit/test_incident_data.py`
- `docs/adr/ADR-0003-dataset-and-provenance.md`
- `docs/data/dataset-constitution.md`
- `docs/data/labeling-guide.md`
- `docs/data/source-manifest.md`
- placeholder folders under `data/`

Validation:

```powershell
python -m pytest .\tests\unit
```

Expected result after this slice is applied:

```text
18 passed
```
