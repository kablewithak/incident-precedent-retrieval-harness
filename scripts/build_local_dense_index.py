"""Build a local-SIE dense index from approved incident cards only."""

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
from incident_precedent_harness.retrieval.dense import DenseIndexStore, build_local_dense_index
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


DEFAULT_INDEX_RELATIVE_PATH = Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a versioned local dense index from approved incident cards."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing data/ and evidence_vault/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional index output path. Defaults under evidence_vault/indexes/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    output = (args.output or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()
    settings = get_settings()
    profile = build_local_sie_embedding_profile(
        timeout_ms=int(settings.sie_timeout_seconds * 1000)
    )
    repository = JsonDatasetRepository(root)
    client = SuperlinkedSIEClient.from_settings(settings)

    try:
        index = build_local_dense_index(
            incidents=repository.load_incidents(),
            client=client,
            embedding_profile=profile,
            trace_id=uuid4(),
        )
    except SemanticInferenceError as error:
        print(
            json.dumps(
                {
                    "index_build_kind": "local_sie_dense_index",
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

    DenseIndexStore.write(index, output)
    print(
        json.dumps(
            {
                "index_build_kind": "local_sie_dense_index",
                "status": "passed",
                "index_path": str(output),
                "index_id": index.manifest.index_id,
                "corpus_incident_count": index.manifest.corpus_incident_count,
                "corpus_fingerprint_sha256": index.manifest.corpus_fingerprint_sha256,
                "embedding_profile_id": index.manifest.embedding_profile.profile_id,
                "vector_dimension": index.manifest.vector_dimension,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
