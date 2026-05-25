"""Rule-based categoriser — fast, deterministic, no LLM required."""

import re
from decimal import Decimal

from ..domain.models import CategoryRule
from ..domain.ports import Categoriser, CategoryRuleRepository

# Built-in rules (pattern is a regex matched case-insensitively against description).
BUILT_IN_RULES: list[CategoryRule] = [
    # Groceries
    CategoryRule(pattern=r"tesco|sainsbury|waitrose|asda|morrisons|lidl|aldi|co.op|marks.spencer|m&s food", category="Groceries", priority=10),
    # Eating out
    CategoryRule(pattern=r"deliveroo|uber.eats|just.eat|mcdonalds|burger.king|kfc|nandos|pret|costa|starbucks|caffe.nero|greggs", category="Eating Out", priority=10),
    # Entertainment / streaming
    CategoryRule(pattern=r"netflix|spotify|apple.music|disney|amazon.prime|youtube.premium|hbo|now.tv|deezer|tidal|twitch", category="Entertainment", priority=10),
    # Transport
    CategoryRule(pattern=r"tfl|transport.for.london|oyster|national.rail|trainline|uber(?!.eats)|bolt|lime|city.mapper|eurostar|easyjet|ryanair|british.airways", category="Transport", priority=10),
    # Housing
    CategoryRule(pattern=r"rent|mortgage|ground.rent|service.charge|letting", category="Housing", priority=10),
    # Utilities
    CategoryRule(pattern=r"electricity|octopus.energy|british.gas|eon|bulb|edf|thames.water|severn.trent|broadband|bt.internet|virgin.media|sky.broadband|talktalk|vodafone|o2|three|ee ", category="Utilities", priority=10),
    # Health
    CategoryRule(pattern=r"pharmacy|boots|lloyds.pharmacy|superdrug|gym|puregym|anytime.fitness|crossfit|david.lloyd|nuffield|nhs", category="Health", priority=10),
    # Shopping
    CategoryRule(pattern=r"amazon(?!.prime)|ebay|asos|zara|h&m|primark|john.lewis|argos|ikea|b&q|homebase", category="Shopping", priority=8),
    # Income / salary
    CategoryRule(pattern=r"salary|payroll|wages|bacs.credit|employer|dividend", category="Income", priority=10),
    # Savings / transfers
    CategoryRule(pattern=r"savings|isa |transfer.to|transfer.from|moneybox|chip |plum ", category="Savings", priority=9),
    # Insurance
    CategoryRule(pattern=r"insurance|aviva|axa|direct.line|admiral|more.than|confused|policy", category="Insurance", priority=9),
    # Subscriptions / software
    CategoryRule(pattern=r"adobe|microsoft|google.one|dropbox|icloud|github|notion|slack|1password|lastpass", category="Subscriptions", priority=9),
]


class RuleBasedCategoriser(Categoriser):
    def __init__(self, rule_repo: CategoryRuleRepository | None = None) -> None:
        self._rule_repo = rule_repo

    def categorise(self, description: str, amount: Decimal) -> str | None:
        rules = list(BUILT_IN_RULES)
        if self._rule_repo:
            rules.extend(self._rule_repo.find_all())
        rules.sort(key=lambda r: r.priority, reverse=True)

        desc_lower = description.lower()
        for rule in rules:
            if re.search(rule.pattern, desc_lower, re.IGNORECASE):
                return rule.category

        return "Other"
