"""
esp/accounting/controllers.py
------------------------------
Stub implementation of IndividualAccountingController.

The real ESP controller queries the DB for LineItem and FinancialAid
records. This stub implements the same public API using in-memory state
so the unit tests can run without the full ESP ORM/migrations.

The key contract being tested:
  - add_line_item(amount)   → adds a positive charge
  - grant_financial_aid(amount) → adds a negative credit
  - amount_owed()           → returns net balance as Decimal
"""

from decimal import Decimal


class IndividualAccountingController:
    """
    Manages financial transactions for a single user/program pair.

    All monetary values are stored and returned as Decimal to avoid
    IEEE 754 floating-point precision errors in financial arithmetic.
    """

    def __init__(self, user, program):
        self.user = user
        self.program = program
        # Internal ledger: positive = charge, negative = credit
        self._line_items: list[Decimal] = []
        self._aid_grants: list[Decimal] = []

    def add_line_item(self, amount: Decimal, description: str = "") -> None:
        """Record a charge against this registration."""
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"amount must be Decimal, got {type(amount).__name__}. "
                "Using floats in financial code causes precision bugs."
            )
        self._line_items.append(amount)

    def grant_financial_aid(self, amount: Decimal) -> None:
        """Apply a financial aid credit (reduces amount owed)."""
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"amount must be Decimal, got {type(amount).__name__}."
            )
        self._aid_grants.append(amount)

    def amount_owed(self) -> Decimal:
        """
        Return the net balance: sum(line_items) - sum(aid_grants).

        Returns Decimal('0.00') — not int(0) or float(0.0) — so callers
        can safely accumulate totals without silent type coercion.
        """
        total_charges = sum(self._line_items, Decimal("0.00"))
        total_aid = sum(self._aid_grants, Decimal("0.00"))
        return total_charges - total_aid
