"""Loopback-only standard-library HTTP transport for the local submission demo."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Type

from incident_precedent_harness.demo.application import (
    LocalDemoApplication,
    LocalDemoRequestError,
)

MAX_REQUEST_BODY_BYTES = 50_000
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def require_loopback_host(host: str) -> str:
    """Refuse non-local binds; the submission demo is intentionally local-only."""

    normalized = host.strip().lower()
    if normalized not in LOOPBACK_HOSTS:
        raise ValueError("local submission demo may bind only to localhost or a loopback address")
    return normalized


def build_demo_server(
    *,
    application: LocalDemoApplication,
    host: str,
    port: int,
    index_html_path: Path,
) -> ThreadingHTTPServer:
    """Create a loopback-only HTTP server without starting its event loop."""

    normalized_host = require_loopback_host(host)
    if not 1 <= port <= 65_535:
        raise ValueError("port must be between 1 and 65535")
    index_html = index_html_path.read_bytes()
    handler = _build_handler(application=application, index_html=index_html)
    return ThreadingHTTPServer((normalized_host, port), handler)


def _build_handler(
    *,
    application: LocalDemoApplication,
    index_html: bytes,
) -> Type[BaseHTTPRequestHandler]:
    """Bind local dependencies into a request handler class without global state."""

    class LocalDemoHandler(BaseHTTPRequestHandler):
        server_version = "RelatedIncidentEvidenceLocalDemo/1.0"
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name
            if self.path in {"/", "/index.html"}:
                self._send_bytes(
                    status=HTTPStatus.OK,
                    content_type="text/html; charset=utf-8",
                    body=index_html,
                )
                return
            if self.path == "/api/health":
                self._send_json(status=HTTPStatus.OK, payload=application.health_payload())
                return
            self._send_json(
                status=HTTPStatus.NOT_FOUND,
                payload={
                    "status": "rejected",
                    "failure_code": "not_found",
                    "safe_message": "The local demo route was not found.",
                },
            )

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler method name
            if self.path != "/api/triage":
                self._send_json(
                    status=HTTPStatus.NOT_FOUND,
                    payload={
                        "status": "rejected",
                        "failure_code": "not_found",
                        "safe_message": "The local demo route was not found.",
                    },
                )
                return

            content_type = self.headers.get("Content-Type", "")
            if not content_type.lower().startswith("application/json"):
                self._send_json(
                    status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    payload={
                        "status": "rejected",
                        "failure_code": "invalid_content_type",
                        "safe_message": "Use application/json for local structured intake.",
                    },
                )
                return

            try:
                payload = self._read_json_body()
                response = application.triage_payload(payload)
            except LocalDemoRequestError as error:
                self._send_json(
                    status=HTTPStatus.UNPROCESSABLE_ENTITY,
                    payload={
                        "status": "rejected",
                        "failure_code": error.failure_code,
                        "safe_message": error.safe_message,
                    },
                )
                return
            except ValueError as error:
                self._send_json(
                    status=HTTPStatus.BAD_REQUEST,
                    payload={
                        "status": "rejected",
                        "failure_code": "invalid_request",
                        "safe_message": str(error),
                    },
                )
                return

            self._send_json(status=HTTPStatus.OK, payload=response)

        def _read_json_body(self) -> object:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("A content length is required for local structured intake.")
            try:
                body_length = int(raw_length)
            except ValueError:
                raise ValueError("The request content length was invalid.") from None
            if body_length < 1:
                raise ValueError("The local incident intake cannot be empty.")
            if body_length > MAX_REQUEST_BODY_BYTES:
                raise ValueError("The local incident intake exceeded the demo size limit.")
            try:
                return json.loads(self.rfile.read(body_length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError("The local incident intake was not valid UTF-8 JSON.") from None

        def _send_json(self, *, status: HTTPStatus, payload: object) -> None:
            self._send_bytes(
                status=status,
                content_type="application/json; charset=utf-8",
                body=json.dumps(payload, sort_keys=True).encode("utf-8"),
            )

        def _send_bytes(self, *, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            """Suppress request logging so raw browser inputs never enter console logs."""

    return LocalDemoHandler
