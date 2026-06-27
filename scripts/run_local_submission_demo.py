"""Run the loopback-only Related Incident Evidence submission demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.config.settings import get_settings
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.demo.application import LocalDemoApplication
from incident_precedent_harness.demo.local_demo_server import build_demo_server
from incident_precedent_harness.inference.profiles import build_local_sie_embedding_profile
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient
from incident_precedent_harness.retrieval.dense import DenseIndexError, DenseIndexStore, DenseRetriever
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.service import TriageService

DEFAULT_INDEX_RELATIVE_PATH = (
    Path("evidence_vault") / "indexes" / "local-sie-dense-index-v1.json"
)
DEFAULT_INDEX_HTML_RELATIVE_PATH = (
    Path("src")
    / "incident_precedent_harness"
    / "demo"
    / "static"
    / "index.html"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local-only Related Incident Evidence submission demo. "
            "The server binds loopback only and stores no browser payloads."
        )
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--index", type=Path, help="Optional explicit local dense-index path.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def build_application(repository_root: Path, index_path: Path) -> LocalDemoApplication:
    """Construct the existing governed triage service for the local demo transport."""

    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    index = DenseIndexStore.load(index_path)
    settings = get_settings()
    if not settings.is_local_sie:
        raise RuntimeError("The local submission demo requires a local SIE endpoint.")
    profile = build_local_sie_embedding_profile(
        timeout_ms=int(settings.sie_timeout_seconds * 1_000)
    )
    service = TriageService(
        incidents=incidents,
        procedures=procedures,
        dense_retriever=DenseRetriever(index=index, incidents=incidents),
        semantic_client=SuperlinkedSIEClient.from_settings(settings),
        embedding_profile=profile,
        policy=AntiAnchoringDecisionPolicy(),
    )
    return LocalDemoApplication(service=service)


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    index_path = (args.index or root / DEFAULT_INDEX_RELATIVE_PATH).resolve()
    index_html_path = root / DEFAULT_INDEX_HTML_RELATIVE_PATH

    if not index_html_path.is_file():
        return _refused("demo_static_asset_missing", "The local demo HTML asset is missing.")

    try:
        application = build_application(root, index_path)
        server = build_demo_server(
            application=application,
            host=args.host,
            port=args.port,
            index_html_path=index_html_path,
        )
    except (DenseIndexError, RuntimeError, ValueError) as error:
        return _refused("demo_setup_invalid", str(error))

    address, port = server.server_address[:2]
    print(
        json.dumps(
            {
                "status": "running",
                "surface_kind": "local_submission_demo",
                "url": f"http://{address}:{port}",
                "bind_scope": "loopback_only",
                "corpus_mode": "synthetic_relayops",
                "procedure_execution_authorized": False,
                "persistence": "none",
            },
            indent=2,
        )
    )
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nLocal demo stopped.")
    finally:
        server.server_close()
    return 0


def _refused(failure_code: str, safe_message: str) -> int:
    print(
        json.dumps(
            {
                "status": "refused",
                "surface_kind": "local_submission_demo",
                "failure_code": failure_code,
                "safe_message": safe_message,
            },
            indent=2,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
