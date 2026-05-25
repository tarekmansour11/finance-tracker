# finance-tracker

A self-hosted personal finance tracker. Import your bank transactions via CSV, get automatic categorisation, subscription detection, and a clean web dashboard — all running locally, no cloud, no open banking.

See [SPEC.md](./SPEC.md) for the full specification and roadmap.

---

## Features (v0.1)

- **CSV import** — bank-agnostic; column names are configurable per export format
- **Auto-categorisation** — rule-based engine (Groceries, Transport, Utilities, etc.) with Ollama LLM fallback for unknowns
- **De-duplication** — reimporting the same CSV never creates duplicate records
- **Subscription detection** — automatically identifies recurring charges and detects price increases
- **Web dashboard** — monthly overview with charts, transaction browser, subscription list
- **CLI** — import, summarise, list subscriptions, launch the dashboard

---

## Architecture

Onion architecture — inner layers have no dependency on outer layers:

```
domain/          → core models and port interfaces (no external deps)
application/     → use cases (import, detect subscriptions, reporting)
infrastructure/  → SQLite repos, CSV reader, rule engine, Ollama client
presentation/    → Typer CLI, FastAPI web app + Jinja2 templates
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) (optional — for LLM categorisation; falls back to rules if not running)

```bash
# Install Ollama, then pull a model
ollama pull mistral
```

### Installation

```bash
git clone https://github.com/tarekmansour11/finance-tracker.git
cd finance-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Usage

### Import a CSV

Your CSV must have at minimum: `date`, `description`, `amount` columns.

```bash
finance-tracker import-csv transactions.csv
```

If your bank uses different column names, remap them:

```bash
finance-tracker import-csv export.csv \
  --date-col "Transaction Date" \
  --desc-col "Narrative" \
  --amount-col "Amount (GBP)"
```

Supported date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `MM/DD/YYYY`.

### View a summary

```bash
finance-tracker summary                  # all months
finance-tracker summary --year 2024 --month 3   # specific month
```

### List subscriptions

```bash
finance-tracker subscriptions
```

### Launch the dashboard

```bash
finance-tracker serve                    # opens http://127.0.0.1:8000
finance-tracker serve --port 9000        # custom port
```

---

## CSV Format

Minimal expected format:

```csv
date,description,amount,currency
2024-01-15,NETFLIX.COM,-15.99,GBP
2024-01-16,SALARY DEPOSIT,3500.00,GBP
```

- Positive amounts = credits (income)
- Negative amounts = debits (spending)
- `currency` column is optional (defaults to GBP)

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=finance_tracker

# Lint
ruff check .
```

### Test fixtures

Fake CSVs live in `tests/fixtures/` — no real financial data is ever committed.

---

## Project Structure

```
src/finance_tracker/
├── domain/
│   ├── models.py          # Transaction, Subscription, CategoryRule, MonthlySummary
│   └── ports.py           # Abstract repository and categoriser interfaces
├── application/
│   ├── import_transactions.py
│   ├── detect_subscriptions.py
│   └── reporting.py
├── infrastructure/
│   ├── database.py        # SQLite implementations of all repos
│   ├── csv_reader.py      # Bank-agnostic CSV parser
│   ├── rule_engine.py     # Keyword-based categoriser
│   └── ollama_client.py   # LLM categoriser (optional, graceful fallback)
└── presentation/
    ├── cli.py             # Typer CLI
    └── web/
        ├── app.py         # FastAPI application
        └── templates/     # Jinja2 HTML templates
tests/
├── domain/
├── application/
├── infrastructure/
└── fixtures/              # Fake CSVs (no real financial data)
```

---

## Privacy

- All data stays on your machine in a local SQLite file (`~/.finance-tracker/finance.db`)
- The `.gitignore` explicitly excludes `*.csv`, `*.ofx`, and `data/` — no accidental data commits
- Ollama runs locally; no transaction data is sent to any external API

---

## License

MIT
