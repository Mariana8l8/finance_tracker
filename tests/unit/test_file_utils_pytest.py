from __future__ import annotations

import logging

import pytest

from finance_tracker.file_utils import logged_operation


def test_logged_operation_writes_success_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        with logged_operation("demo operation"):
            result = 2 + 2

    assert result == 4
    assert "demo operation started" in caplog.text
    assert "demo operation finished" in caplog.text


def test_logged_operation_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(RuntimeError, match="boom"):
        with caplog.at_level(logging.ERROR):
            with logged_operation("failing operation"):
                raise RuntimeError("boom")

    assert "failing operation failed" in caplog.text
