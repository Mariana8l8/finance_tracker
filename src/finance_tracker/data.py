"""Structured finance data for laboratory work 2."""

Transaction = dict[str, object]

TRANSACTION_TYPES: tuple[str, ...] = ("income", "expense")
EXPENSE_TYPES: set[str] = {"expense"}

transactions: list[Transaction] = [
    {
        "id": 1,
        "date": "2026-09-01",
        "category": "Salary",
        "amount": 32000.00,
        "type": "income",
        "description": "Monthly salary",
    },
    {
        "id": 2,
        "date": "2026-09-03",
        "category": "Food",
        "amount": 1850.50,
        "type": "expense",
        "description": "Groceries",
    },
    {
        "id": 3,
        "date": "2026-09-05",
        "category": "Transport",
        "amount": 620.00,
        "type": "expense",
        "description": "Public transport",
    },
    {
        "id": 4,
        "date": "2026-09-07",
        "category": "Freelance",
        "amount": 7600.00,
        "type": "income",
        "description": "Landing page project",
    },
    {
        "id": 5,
        "date": "2026-09-09",
        "category": "Food",
        "amount": 980.25,
        "type": "expense",
        "description": "Lunch and household items",
    },
    {
        "id": 6,
        "date": "2026-09-11",
        "category": "Education",
        "amount": 2100.00,
        "type": "expense",
        "description": "Courses and books",
    },
    {
        "id": 7,
        "date": "2026-09-12",
        "category": "Bonus",
        "amount": 4500.00,
        "type": "income",
        "description": "Project bonus",
    },
]
