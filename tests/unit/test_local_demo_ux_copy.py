"""Regression checks for the human-first local demo presentation layer."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_HTML = (
    ROOT
    / "src"
    / "incident_precedent_harness"
    / "demo"
    / "static"
    / "index.html"
)


def test_demo_uses_plain_language_controls_and_collapses_advanced_selection() -> None:
    content = DEMO_HTML.read_text(encoding="utf-8")

    assert "What have we confirmed?" in content
    assert "Advanced: choose the closest past example" in content
    assert "<details>\n            <summary>Advanced: choose the closest past example</summary>" in content
    assert "Structured verification facts" not in content
    assert "Optional representative-selection evidence" not in content


def test_demo_makes_human_review_and_no_execution_limit_visible() -> None:
    content = DEMO_HTML.read_text(encoding="utf-8")

    assert "Human review required." in content
    assert "No procedure will run automatically." in content
    assert "Review only." in content
    assert "Inspect technical details" in content
