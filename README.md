# Finance Tracker

Laboratory project for the Professional Python course.

Variant 12 uses one cross-lab domain: finance tracker.

- Laboratory work 1: project structure and basic finance tracker logic.
- Laboratory work 2: structured finance transaction analysis.
- Laboratory work 3: streaming transaction processing.
- Laboratory work 4: professional typed OOP domain model.
- Laboratory work 5: reliable CSV import, YAML configuration, logging and JSON export.

## Description

Console application for finance tracking laboratory works. The project
demonstrates src-layout packaging, structured data processing, streaming I/O,
typed OOP design, custom exceptions, configuration, logging, validation and
atomic export.

The current entry point demonstrates the laboratory work 5 reliable file
pipeline.

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Run

```bash
python -m finance_tracker.main
```

or:

```bash
finance-tracker
```

## Tests

```bash
python -m unittest discover -s tests
python -m mypy src
```

## Laboratory 5 Files

```text
config/lab5_config.yaml
examples/lab5_transactions.csv
src/finance_tracker/exceptions.py
src/finance_tracker/config.py
src/finance_tracker/logging_config.py
src/finance_tracker/file_utils.py
src/finance_tracker/file_pipeline.py
src/finance_tracker/file_exporters.py
tests/test_file_pipeline.py
```

## Author

Student: Roman Mariana
Group: FEP-32
