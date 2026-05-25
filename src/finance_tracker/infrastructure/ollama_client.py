"""Ollama-backed categoriser — uses a local LLM as a fallback for unknown transactions.

Falls back gracefully to None if Ollama is not running, so the rule engine
can handle it instead (or leave as "Other").
"""

from decimal import Decimal

from ..domain.ports import Categoriser

KNOWN_CATEGORIES = [
    "Groceries",
    "Eating Out",
    "Entertainment",
    "Transport",
    "Housing",
    "Utilities",
    "Health",
    "Shopping",
    "Income",
    "Savings",
    "Insurance",
    "Subscriptions",
    "Other",
]

_PROMPT_TEMPLATE = """You are a personal finance assistant. Categorise the following bank transaction into exactly one of these categories:

{categories}

Transaction description: "{description}"
Amount: {amount} GBP

Reply with ONLY the category name, nothing else."""


class OllamaCategoriser(Categoriser):
    """Calls a locally-running Ollama model to categorise transactions.

    Args:
        model: Ollama model name (e.g. "mistral", "llama3", "phi3").
        fallback: Categoriser to use if Ollama is unavailable (typically the rule engine).
    """

    def __init__(self, model: str = "mistral", fallback: Categoriser | None = None) -> None:
        self._model = model
        self._fallback = fallback
        self._cache: dict[str, str] = {}  # description -> category

    def categorise(self, description: str, amount: Decimal) -> str | None:
        key = description.strip().upper()
        if key in self._cache:
            return self._cache[key]

        try:
            import ollama  # imported lazily so the app works without Ollama installed

            prompt = _PROMPT_TEMPLATE.format(
                categories="\n".join(f"- {c}" for c in KNOWN_CATEGORIES),
                description=description,
                amount=amount,
            )
            response = ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response["message"]["content"].strip()
            category = self._extract_category(raw)
            self._cache[key] = category
            return category

        except Exception:
            # Ollama not running, model not found, or any other error → fall back.
            if self._fallback:
                return self._fallback.categorise(description, amount)
            return None

    def _extract_category(self, raw: str) -> str:
        for cat in KNOWN_CATEGORIES:
            if cat.lower() in raw.lower():
                return cat
        return "Other"
