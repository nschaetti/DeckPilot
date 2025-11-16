"""Tests for the enhanced logging filter system."""

from __future__ import annotations

import pytest

from deckpilot.utils.logger import (
    LogEntry,
    LogFilterRule,
    LogLevel,
    Logger,
    setup_logger,
)


@pytest.fixture()
def reset_logger():
    """Ensure each test works with a fresh singleton instance."""

    Logger._instance = None
    yield
    Logger._instance = None


def test_filter_rule_combines_level_and_source(reset_logger):
    rule = LogFilterRule.from_spec("type=INFO|WARNING,source=Panel.*")

    entry_ok = LogEntry(LogLevel.INFO, "INFO", "PanelMain", "ready")
    entry_bad_level = LogEntry(LogLevel.DEBUG, "DEBUG", "PanelMain", "ignored")
    entry_bad_source = LogEntry(LogLevel.INFO, "INFO", "Other", "ignored")

    assert rule.matches(entry_ok)
    assert not rule.matches(entry_bad_level)
    assert not rule.matches(entry_bad_source)


def test_logger_applies_and_filters_entries(monkeypatch, reset_logger):
    logger = setup_logger(level="DEBUG", filters=["type=INFO,source=Panel.*"])

    captured: list[str] = []

    def fake_log(message, *args, **kwargs):
        captured.append(message)

    monkeypatch.setattr(logger._console, "log", fake_log)

    logger.info("panel active", source="PanelMain")
    logger.info("other panel", source="Other")
    logger.warning("panel warning", source="PanelMain")

    assert len(captured) == 1
    assert "panel active" in captured[0]


def test_multiple_filters_work_as_or(monkeypatch, reset_logger):
    logger = setup_logger(level="DEBUG", filters=["type=ERROR", "source=Panel.*"])
    captured: list[str] = []

    def fake_log(message, *args, **kwargs):
        captured.append(message)

    monkeypatch.setattr(logger._console, "log", fake_log)

    logger.info("panel info shown", source="PanelMain")
    logger.error("error anywhere", source="Other")
    logger.warning("ignored warning", source="Other")

    assert len(captured) == 2
    assert any("panel info shown" in msg for msg in captured)
    assert any("error anywhere" in msg for msg in captured)


def test_level_and_source_columns_are_padded(reset_logger):
    logger = setup_logger(level="INFO")

    level_col = logger._format_level("WARN", None)
    assert len(level_col) == logger._LEVEL_COL_WIDTH

    source_col = logger._format_source("AssetManager")
    stripped = source_col.replace("[dim]", "").replace("[/]", "")
    assert len(stripped) == logger._SOURCE_COL_WIDTH
