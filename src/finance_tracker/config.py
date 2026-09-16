"""YAML configuration loading for laboratory work 5."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Mapping

from finance_tracker.exceptions import ConfigurationError


DEFAULT_CONFIG_PATH = Path("config") / "lab5_config.yaml"


@dataclass(frozen=True, slots=True)
class InputConfig:
    """Input file configuration."""

    path: Path
    format: str


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Output file configuration."""

    path: Path
    format: str


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Validation and processing policy configuration."""

    skip_invalid: bool
    minimum_amount: float
    allowed_types: frozenset[str]


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Logging configuration."""

    level: str
    file: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Full import/export application configuration."""

    input: InputConfig
    output: OutputConfig
    processing: ProcessingConfig
    logging: LoggingConfig


@dataclass(frozen=True, slots=True)
class ProductionSettings:
    """Environment-driven settings for production-oriented runs."""

    app_name: str
    environment: str
    database_url: str
    log_level: str


DEFAULT_DATABASE_URL = "sqlite:///data/finance_tracker.db"
DEFAULT_APP_NAME = "Finance Tracker API"


YamlValue = str | int | float | bool
YamlSection = dict[str, YamlValue]
YamlDocument = dict[str, YamlSection]


def load_config(
    path: Path,
) -> AppConfig:
    """Load and validate a small YAML configuration file."""

    if not path.exists():
        raise ConfigurationError(f"Configuration file does not exist: {path}")

    try:
        raw_config = _read_simple_yaml(path)
    except OSError as error:
        raise ConfigurationError(f"Cannot read configuration file: {path}") from error
    except ValueError as error:
        raise ConfigurationError(f"Invalid YAML configuration: {path}") from error

    base = path.parent
    config = AppConfig(
        input=InputConfig(
            path=_resolve_path(base, _required_str(raw_config, "input", "path")),
            format=_required_str(raw_config, "input", "format"),
        ),
        output=OutputConfig(
            path=_resolve_path(base, _required_str(raw_config, "output", "path")),
            format=_required_str(raw_config, "output", "format"),
        ),
        processing=ProcessingConfig(
            skip_invalid=_required_bool(raw_config, "processing", "skip_invalid"),
            minimum_amount=_required_float(raw_config, "processing", "minimum_amount"),
            allowed_types=_required_set(raw_config, "processing", "allowed_types"),
        ),
        logging=LoggingConfig(
            level=_required_str(raw_config, "logging", "level"),
            file=_resolve_path(base, _required_str(raw_config, "logging", "file")),
        ),
    )
    validate_config(config)
    return config


def get_config_path(
    env_var: str = "FINANCE_TRACKER_CONFIG",
) -> Path:
    """Return config path from environment or the default project path."""

    value = os.getenv(env_var)
    if value is None or not value.strip():
        return DEFAULT_CONFIG_PATH
    return Path(value)


@lru_cache(maxsize=1)
def get_settings() -> ProductionSettings:
    """Load production-oriented settings from environment variables."""

    return ProductionSettings(
        app_name=_env("FINANCE_TRACKER_APP_NAME", DEFAULT_APP_NAME),
        environment=_env("APP_ENV", "development"),
        database_url=_env("DATABASE_URL", DEFAULT_DATABASE_URL),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
    )


def validate_config(
    config: AppConfig,
) -> None:
    """Fail fast when configuration cannot produce a reliable run."""

    if config.input.format != "csv":
        raise ConfigurationError("Only CSV input is supported.")
    if config.output.format != "json":
        raise ConfigurationError("Only JSON output is supported.")
    if not config.input.path.exists():
        raise ConfigurationError(f"Input file does not exist: {config.input.path}")
    if config.processing.minimum_amount < 0:
        raise ConfigurationError("minimum_amount must not be negative.")
    if not config.processing.allowed_types:
        raise ConfigurationError("allowed_types must not be empty.")
    unknown_types = config.processing.allowed_types - {"income", "expense"}
    if unknown_types:
        raise ConfigurationError(f"Unknown transaction types: {sorted(unknown_types)}")


def _read_simple_yaml(
    path: Path,
) -> YamlDocument:
    """Read the YAML subset used by the lab config.

    The project intentionally avoids an external PyYAML dependency so automated
    checks can run from a fresh editable install.
    """

    document: YamlDocument = {}
    current_section: str | None = None

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue

            if not raw_line.startswith((" ", "\t")):
                if not line.endswith(":"):
                    raise ValueError(f"Line {line_number}: expected section.")
                current_section = line[:-1].strip()
                if not current_section:
                    raise ValueError(f"Line {line_number}: empty section.")
                document[current_section] = {}
                continue

            if current_section is None:
                raise ValueError(f"Line {line_number}: key without section.")

            stripped = line.strip()
            if ":" not in stripped:
                raise ValueError(f"Line {line_number}: expected key-value pair.")
            key, value = stripped.split(":", 1)
            key = key.strip()
            if not key:
                raise ValueError(f"Line {line_number}: empty key.")
            document[current_section][key] = _parse_scalar(value.strip())

    return document


def _parse_scalar(
    value: str,
) -> YamlValue:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if len(value) >= 2 and value[0] == value[-1] and value.startswith(("'", '"')):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _env(
    name: str,
    default: str,
) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _section(
    document: Mapping[str, YamlSection],
    section: str,
) -> YamlSection:
    try:
        return document[section]
    except KeyError as error:
        raise ConfigurationError(f"Missing configuration section: {section}") from error


def _required_str(
    document: Mapping[str, YamlSection],
    section: str,
    key: str,
) -> str:
    values = _section(document, section)
    try:
        value = values[key]
    except KeyError as error:
        raise ConfigurationError(f"Missing configuration key: {section}.{key}") from error
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{section}.{key} must be a non-empty string.")
    return value


def _required_bool(
    document: Mapping[str, YamlSection],
    section: str,
    key: str,
) -> bool:
    values = _section(document, section)
    try:
        value = values[key]
    except KeyError as error:
        raise ConfigurationError(f"Missing configuration key: {section}.{key}") from error
    if not isinstance(value, bool):
        raise ConfigurationError(f"{section}.{key} must be a boolean.")
    return value


def _required_float(
    document: Mapping[str, YamlSection],
    section: str,
    key: str,
) -> float:
    values = _section(document, section)
    try:
        value = values[key]
    except KeyError as error:
        raise ConfigurationError(f"Missing configuration key: {section}.{key}") from error
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{section}.{key} must be numeric.")
    return float(value)


def _required_set(
    document: Mapping[str, YamlSection],
    section: str,
    key: str,
) -> frozenset[str]:
    raw_value = _required_str(document, section, key)
    return frozenset(item.strip() for item in raw_value.split(",") if item.strip())


def _resolve_path(
    base: Path,
    value: str,
) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()
