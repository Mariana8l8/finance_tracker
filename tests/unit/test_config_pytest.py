from __future__ import annotations

from pathlib import Path

import pytest

from finance_tracker.config import DEFAULT_CONFIG_PATH, get_config_path, load_config
from finance_tracker.exceptions import ConfigurationError


def write_config(
    tmp_path: Path,
    *,
    input_path: Path,
    input_format: str = "csv",
    output_format: str = "json",
    minimum_amount: str = "0",
    allowed_types: str = "income,expense",
) -> Path:
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "input:",
                f"  path: {input_path}",
                f"  format: {input_format}",
                "output:",
                "  path: output.json",
                f"  format: {output_format}",
                "processing:",
                "  skip_invalid: true",
                f"  minimum_amount: {minimum_amount}",
                f"  allowed_types: {allowed_types}",
                "logging:",
                "  level: INFO",
                "  file: app.log",
            ]
        ),
        encoding="utf-8",
    )
    return config


def test_get_config_path_uses_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINANCE_TRACKER_CONFIG", "custom.yaml")

    assert get_config_path() == Path("custom.yaml")


def test_get_config_path_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FINANCE_TRACKER_CONFIG", raising=False)

    assert get_config_path() == DEFAULT_CONFIG_PATH


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text("transaction_id,date,type,category,amount,description\n", encoding="utf-8")
    config_path = write_config(tmp_path, input_path=csv_path.name)

    config = load_config(config_path)

    assert config.input.path == csv_path.resolve()
    assert config.output.path == (tmp_path / "output.json").resolve()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        pytest.param("input_format", "json", "Only CSV", id="bad-input-format"),
        pytest.param("output_format", "csv", "Only JSON", id="bad-output-format"),
        pytest.param("minimum_amount", "-1", "minimum_amount", id="negative-minimum"),
        pytest.param("allowed_types", "income,transfer", "Unknown transaction", id="unknown-type"),
    ],
)
def test_load_config_rejects_invalid_values(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text("transaction_id,date,type,category,amount,description\n", encoding="utf-8")
    kwargs = {
        "input_path": csv_path.name,
        field: value,
    }
    config_path = write_config(tmp_path, **kwargs)

    with pytest.raises(ConfigurationError, match=message):
        load_config(config_path)


def test_load_config_rejects_malformed_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.yaml"
    config_path.write_text("input path without section", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        load_config(config_path)
