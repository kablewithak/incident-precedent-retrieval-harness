"""Check local SIE liveness and readiness without making inference claims."""

from __future__ import annotations

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from incident_precedent_harness.config import get_settings


def check_endpoint(url: str, timeout_seconds: float) -> dict[str, object]:
    """Return a minimal, safe endpoint result without logging response payloads."""
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310
            status_code = response.status
    except HTTPError as error:
        status_code = error.code
    except URLError as error:
        return {
            "endpoint": url,
            "reachable": False,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "error_type": type(error.reason).__name__,
        }

    return {
        "endpoint": url,
        "reachable": status_code == 200,
        "status_code": status_code,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }


def main() -> int:
    """Execute the local health check."""
    settings = get_settings()
    base_url = settings.sie_base_url
    results = [
        check_endpoint(f"{base_url}/healthz", settings.sie_timeout_seconds),
        check_endpoint(f"{base_url}/readyz", settings.sie_timeout_seconds),
    ]
    print(json.dumps({"sie_base_url": base_url, "checks": results}, indent=2))
    return 0 if all(result["reachable"] for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
