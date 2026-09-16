"""Application-specific exception hierarchy for reliable file processing."""


class FinanceTrackerError(Exception):
    """Base application error."""


class ConfigurationError(FinanceTrackerError):
    """Raised when application configuration is missing or invalid."""


class DataError(FinanceTrackerError):
    """Base error for import and export failures."""


class DataImportError(DataError):
    """Raised when external data cannot be imported."""


class DataExportError(DataError):
    """Raised when external data cannot be exported safely."""


class RecordValidationError(DataImportError):
    """Raised when one external row cannot be converted to a valid record."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.line_number is not None:
            parts.append(f"line={self.line_number}")
        if self.field is not None:
            parts.append(f"field={self.field}")
        return " | ".join(parts)
