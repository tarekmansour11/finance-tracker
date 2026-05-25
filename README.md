# finance-tracker

A self-hosted personal finance tracker. Import your bank transactions, categorise spending automatically, and get a clear picture of where your money goes — without handing your data to a third party.

---

## Project Purpose

Most finance apps either require open banking access or lock your data in their cloud. This project takes the opposite approach: you export your transactions (CSV, OFX, or similar), run this tool locally, and get clean insights with no external dependencies beyond what you install yourself.

---

## Planned Features

- [ ] Import transactions from CSV exports (Monzo, Starling, HSBC formats)
- [ ] Auto-categorisation of transactions using rule-based and ML-assisted matching
- [ ] Monthly spending summaries by category
- [ ] Budget targets with over/under tracking
- [ ] Simple CLI interface for querying and reporting
- [ ] Optional web dashboard (local-only)
- [ ] Export reports to CSV or PDF

> **TODO:** Define the full feature set and prioritise the roadmap before v0.1.

---

## Project Structure

```
finance-tracker/
├── src/
│   └── finance_tracker/
│       ├── __init__.py
│       ├── models.py        # Data models (Transaction, Category, Budget)
│       ├── importers/       # Format-specific CSV/OFX importers
│       ├── categoriser.py   # Rule-based categorisation logic
│       └── reports.py       # Summary and reporting functions
├── tests/
├── main.py                  # CLI entry point
├── pyproject.toml
├── .gitignore
└── CHANGELOG.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
git clone https://github.com/tarekmansour11/finance-tracker.git
cd finance-tracker

# With uv
uv sync

# Or with pip
pip install -e .
```

### Running

```bash
python main.py --help
```

---

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
pytest

# Lint & format
ruff check .
ruff format .
```

---

## Contributing

This is a personal project — contributions aren't expected, but issues and ideas are welcome.

---

## License

MIT
