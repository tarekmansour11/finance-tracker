# finance-tracker: Specification

## Vision

A **local-first personal finance tool** that gives you a clear picture of where your money goes — without handing your data to the cloud, requiring open banking access, or dealing with bank-specific nonsense.

You own your data. It stays on your machine. Simple.

---

## Project Purpose

Most finance apps fail in one of two ways:
- **Cloud + open banking** (Emma, Snoop): Your bank credentials live on someone else's servers. Sketchy.
- **Spreadsheets**: Tedious to maintain, zero intelligence.

This fills the gap: **local-first + intelligent**. You export a CSV from your bank, the tool ingests it, categorises it, detects patterns (subscriptions, spending trends), and lets you ask questions about your data in plain English.

---

## Core Features (v0.1)

### 1. CSV Import (Bank-Agnostic)
- Accept a standardised CSV schema: `date`, `description`, `amount`, `currency`
- Provide a lightweight config file for users to map their bank's columns to the schema
- Support multiple imports — append new transactions, skip duplicates
- Example:
  ```csv
  date,description,amount,currency
  2024-01-15,NETFLIX.COM,-15.99,GBP
  2024-01-16,SALARY DEPOSIT,3500.00,GBP
  ```

### 2. Auto-Categorisation
- **Rule-based layer** (fast, deterministic):
  - Merchant keyword matching (e.g., "TESCO" → Groceries, "SPOTIFY" → Entertainment)
  - Configurable rules in YAML/JSON
- **LLM layer** (Ollama, local):
  - For transactions the rules don't match, ask the LLM to categorise
  - Prompt: "Categorise this transaction. Description: {description}, Amount: {amount}. Categories: [Groceries, Transport, Utilities, Entertainment, etc.]"
  - Cache results — don't re-categorise the same merchant twice

### 3. Subscription Detection
- Identify recurring charges automatically by scanning transaction history
- Logic: same merchant, similar amount (allow ±10%), regular interval (weekly/monthly/yearly)
- Detect price changes ("Netflix went from £9.99 → £12.99")
- Display in a dedicated view with cancel recommendations

### 4. HTML Dashboard
- **Monthly overview**: Pie chart of spend by category
- **Month-over-month**: Bar chart of category trends (this month vs. last month)
- **Subscription list**: All recurring charges with next charge date and annual cost
- **Recent transactions**: Table view with filters by category
- **Summary card**: Total spend, average transaction, largest transaction

### 5. Natural Language Q&A
- Accept text queries like: "What did I spend on food in March?" or "How much have I paid for subscriptions this year?"
- Use Ollama to generate a SQL query or answer from the data
- Return a human-readable response

---

## Technology Stack

**Backend:**
- Python 3.11+
- SQLite (storage, zero setup)
- Typer (CLI)
- FastAPI (HTTP server for dashboard)
- SQLAlchemy or `sqlite-utils` (ORM/querying)
- Ollama (local LLM inference)

**Frontend:**
- Simple HTML/CSS/JavaScript (vanilla or lightweight framework)
- Served by FastAPI; static assets or Jinja2 templates

**Data Pipeline:**
- `pandas` for CSV parsing and validation
- Rule engine (simple dict-based or more sophisticated)

---

## Out of Scope (v0.1)

- Budget targets and alerts
- Multi-user/family sharing
- Investments, crypto, stocks
- Multi-currency edge cases (FX conversion)
- Mobile app
- Open banking integrations (defeats the purpose)
- Bank-specific importers (Monzo, Starling, etc.)

---

## Data Model

### Transaction
```python
{
  id: str (uuid),
  date: date,
  description: str,
  amount: Decimal,
  currency: str,
  category: str (optional, filled by categoriser),
  merchant: str (optional, extracted from description),
  is_recurring: bool,
  created_at: datetime,
  updated_at: datetime,
}
```

### Subscription
```python
{
  id: str,
  merchant: str,
  category: str,
  amount: Decimal,
  frequency: str (weekly | monthly | yearly),
  next_charge_date: date,
  detected_at: datetime,
  price_history: list[{date, amount}],
}
```

### CategoryRule
```python
{
  id: str,
  pattern: str (regex or substring),
  category: str,
  priority: int (higher = checked first),
  created_by: str (user | system),
}
```

---

## User Journey (MVP)

1. **Setup**
   ```bash
   finance-tracker init          # Create config file, DB
   ```

2. **First import**
   ```bash
   finance-tracker import data/transactions.csv
   # Tool maps columns, imports, categorises
   ```

3. **View dashboard**
   ```bash
   finance-tracker serve         # Start web server, open http://localhost:8000
   ```

4. **Ask a question**
   ```bash
   finance-tracker ask "How much did I spend on groceries last month?"
   # LLM answers based on your data
   ```

---

## Implementation Roadmap

### Phase 1: Foundation
- [x] Project scaffold (done)
- [ ] Data models (Transaction, Subscription, CategoryRule)
- [ ] SQLite schema and migrations
- [ ] CSV importer with column mapping
- [ ] Basic CLI (`init`, `import`)

### Phase 2: Categorisation
- [ ] Rule-based categoriser with YAML config
- [ ] Ollama integration + prompting
- [ ] Category caching (don't re-ask for same merchant)
- [ ] CLI to test/refine rules

### Phase 3: Intelligence
- [ ] Subscription detection algorithm
- [ ] Price change detection
- [ ] Basic reporting functions

### Phase 4: Dashboard
- [ ] FastAPI server setup
- [ ] HTML templates (overview, subscriptions, recent)
- [ ] Charts (matplotlib, plotly, or lightweight JS lib)
- [ ] Responsive design

### Phase 5: Polish
- [ ] Q&A with Ollama
- [ ] Error handling and logging
- [ ] Tests and docs
- [ ] Performance optimisations (if needed)

---

## Notes for Developers

- **Keep it simple.** This is a personal tool. One user, one machine, one database file.
- **Ollama workflow:** Install Ollama, pull a model (`ollama pull mistral`), it runs on localhost:11434. Your app talks to it via Python client.
- **Config file:** Store rules and settings in a simple YAML or JSON file in `~/.finance-tracker/config.json`. Easy to edit, version control, share.
- **No external APIs.** Everything runs locally. No rate limits, no third-party calls (except Ollama, which is local).
- **Transaction de-duplication:** Use a hash of (date, description, amount) to detect reimports.

---

## Success Criteria

By v0.1 launch:
- [ ] Can import a CSV, categorise transactions (rule + LLM), and view them in the dashboard
- [ ] Subscriptions are detected and surfaced
- [ ] Dashboard shows meaningful summaries and charts
- [ ] Can ask a natural language question and get an answer
- [ ] No external APIs; everything is local
- [ ] Clear, simple codebase anyone can extend
