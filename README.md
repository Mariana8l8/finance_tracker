# Finance Tracker

Лабораторна робота №1 з курсу "Професійний Python".

Варіант №12:

- Лабораторна робота №1: фінансовий трекер.
- Лабораторна робота №2: аналіз фінансових транзакцій.
- Лабораторна робота №3: потокова обробка фінансових транзакцій.
- Лабораторна робота №4: професійна ООП-модель фінансового трекера.

## Description

Console application for laboratory works in Professional Python.
The project demonstrates src-layout, data models, business logic,
structured finance data processing, type hints, tests and a command-line entry point.
The current entry point demonstrates the laboratory work 3 streaming pipeline.
The current entry point demonstrates the laboratory work 4 OOP domain model.

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
python -m pip install -e .
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
```

## Project Structure

```text
src/finance_tracker/models.py
src/finance_tracker/services.py
src/finance_tracker/data.py
src/finance_tracker/processors.py
src/finance_tracker/analytics.py
src/finance_tracker/decorators.py
src/finance_tracker/benchmark.py
src/finance_tracker/stream_data.py
src/finance_tracker/stream_models.py
src/finance_tracker/stream_readers.py
src/finance_tracker/stream_filters.py
src/finance_tracker/stream_batches.py
src/finance_tracker/stream_pipeline.py
src/finance_tracker/stream_analytics.py
src/finance_tracker/value_objects.py
src/finance_tracker/domain.py
src/finance_tracker/protocols.py
src/finance_tracker/repositories.py
src/finance_tracker/dto.py
src/finance_tracker/policies.py
src/finance_tracker/oop_services.py
src/finance_tracker/main.py
tests/test_services.py
tests/test_finance_analysis.py
tests/test_stream_pipeline.py
tests/test_oop_domain.py
```

## Author

Student: Roman Mariana
Group: FEP-32
