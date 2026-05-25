# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/).

---

## [0.1.0] - 2024-05-25

### Added

**Architecture**
- Onion architecture with four layers: domain, application, infrastructure, presentation
- Domain models: `Transaction`, `Subscription`, `CategoryRule`, `MonthlySummary`, `PricePoint`
- Abstract port interfaces for all repositories and the categoriser

**Import**
- Bank-agnostic CSV reader with configurable column mapping
- Supports date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `MM/DD/YYYY`
- Graceful error reporting per row — bad rows are skipped with a message, good rows are imported
- Import de-duplication by (date, description, amount) — safe to re-import the same file

**Categorisation**
- Rule-based categoriser covering: Groceries, Eating Out, Entertainment, Transport, Housing, Utilities, Health, Shopping, Income, Savings, Insurance, Subscriptions
- Ollama LLM categoriser for unknown transactions, with cache to avoid re-querying the same merchant
- Graceful fallback to rule engine if Ollama is not running

**Subscription Detection**
- Automatically identifies recurring debits (weekly / monthly / yearly) from transaction history
- Detects price increases across the price history of each subscription
- Calculates annual cost and next expected charge date
- Persisted to SQLite and refreshed on each import

**Dashboard (web)**
- FastAPI server with Jinja2 templates
- Overview page: stat cards (total spent, income, net, subscription count), doughnut chart by category, month-over-month bar chart, recent transactions
- Transactions page: full list with search and category filter
- Subscriptions page: table with annual cost, frequency, next charge date, price-rise flag

**CLI**
- `finance-tracker import-csv` — import with optional column remapping
- `finance-tracker summary` — rich terminal table, all months or a specific month
- `finance-tracker subscriptions` — subscription list with annual totals
- `finance-tracker serve` — launch the web dashboard

**Testing**
- 51 tests covering all layers
- Fake CSV fixtures in `tests/fixtures/` — no real financial data committed
- In-memory SQLite for all database tests (fast, isolated)

**Infrastructure**
- SQLite storage via raw `sqlite3` (no ORM overhead)
- `.gitignore` explicitly excludes `*.csv`, `*.ofx`, `data/` to prevent accidental data commits
