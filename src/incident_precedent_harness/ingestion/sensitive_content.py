"""Fail-closed sensitive-content detection for staged import candidates.

This is not a DLP product. It intentionally covers a small set of high-risk,
well-defined patterns and rejects the record rather than silently altering
historical evidence. Matched text is never returned.
"""

from __future__ import annotations

import re

from incident_precedent_harness.ingestion.models import (
    SensitiveContentCode,
    SensitiveContentFinding,
)

_DETECTORS: tuple[tuple[SensitiveContentCode, re.Pattern[str]], ...] = (
    (
        SensitiveContentCode.API_KEY_ASSIGNMENT,
        re.compile(r"\b(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    ),
    (
        SensitiveContentCode.BEARER_TOKEN,
        re.compile(r"\bbearer\s+[a-z0-9._~+/-]{12,}", re.IGNORECASE),
    ),
    (
        SensitiveContentCode.CREDENTIAL_URL,
        re.compile(r"\bhttps?://[^\s/@:]+:[^\s/@]+@", re.IGNORECASE),
    ),
    (
        SensitiveContentCode.EMAIL_ADDRESS,
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    (
        SensitiveContentCode.IPV4_ADDRESS,
        re.compile(r"\b(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}\b"),
    ),
    (
        SensitiveContentCode.PASSWORD_ASSIGNMENT,
        re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
    ),
)


def find_sensitive_content(
    *,
    title: str,
    summary: str,
    source_reference: str,
) -> tuple[SensitiveContentFinding, ...]:
    """Return safe finding codes and field names without returning matched content."""

    findings: list[SensitiveContentFinding] = []
    for field_name, value in (
        ("title", title),
        ("summary", summary),
        ("source_reference", source_reference),
    ):
        for code, pattern in _DETECTORS:
            if pattern.search(value):
                findings.append(SensitiveContentFinding(field_name=field_name, code=code))
    return tuple(findings)
