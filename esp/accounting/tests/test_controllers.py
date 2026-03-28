"""
esp/accounting/tests/test_controllers.py
-----------------------------------------
GSoC Proposal: Unit tests for IndividualAccountingController.

WHY THESE TESTS MATTER:
ESP's accounting controllers handle financial aid grants, line items, and
balance calculations for students. Bugs here have real financial consequences.
The existing test coverage for this layer is sparse and uses float arithmetic,
which introduces silent precision errors (e.g., 0.1 + 0.2 != 0.3 in IEEE 754).

This test module demonstrates:
  1. Inheriting CacheFlushTestCase to prevent cached financial state from
     leaking between tests (critical — ESP caches per-user accounting data)
  2. Using Python's Decimal type for all monetary values (PEP 327 compliance)
  3. Testing both the happy path and a compound scenario (line item + aid)
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

# WHY CacheFlushTestCase:
# ESP's accounting layer caches computed balances (amount_owed, line items)
# in Django's cache backend for performance. Without flushing between tests,
# a cached value from test_A can be returned in test_B, causing false passes
# or false failures that are nearly impossible to debug.
# CacheFlushTestCase.setUp()/tearDown() calls cache.clear() automatically.
from esp.tests.util import CacheFlushTestCase

# The controller under test.
# IndividualAccountingController encapsulates all financial operations
# for a single user/program registration pair.
from esp.accounting.controllers import IndividualAccountingController


class TestIndividualAccountingController(CacheFlushTestCase):
    """
    Unit tests for IndividualAccountingController.

    WHY unit tests (not integration tests) here:
    The controller's logic — summing line items, applying aid, computing
    balances — is pure business logic that should be testable without a
    full HTTP request cycle. Unit tests run ~100x faster and pinpoint
    failures precisely.

    We mock the DB layer where needed so tests remain fast and isolated.
    """

    def setUp(self):
        """
        Create a minimal controller instance for each test.

        WHY call super().setUp():
        CacheFlushTestCase.setUp() calls cache.clear(). Skipping super()
        would silently disable the cache flush guarantee.
        """
        super().setUp()

        # Use MagicMock for the user/program dependencies so this test
        # doesn't require a fully migrated DB or fixture files.
        # The controller's arithmetic logic is what we're testing, not ORM queries.
        self.mock_user = MagicMock()
        self.mock_user.id = 1

        self.mock_program = MagicMock()
        self.mock_program.id = 42

        self.controller = IndividualAccountingController(
            user=self.mock_user,
            program=self.mock_program,
        )

    def test_grant_financial_aid_reduces_amount_owed(self):
        """
        Granting $50 of financial aid with no prior line items should
        result in amount_owed() == -$50 (a credit balance).

        WHY Decimal('50.00') not 50.0:
        Float 50.0 is represented as 50.000000000000000 in IEEE 754, but
        compound operations (e.g., 0.1 * 3) produce 0.30000000000000004.
        In financial code this is unacceptable — a student could be charged
        $0.01 too much or too little due to rounding drift.

        Decimal('50.00') is exact. It stores the value as-is and performs
        arithmetic with configurable precision (default 28 significant digits).
        This matches how ESP stores monetary values in the DB (DecimalField).
        """
        aid_amount = Decimal("50.00")

        self.controller.grant_financial_aid(aid_amount)

        # A pure aid grant with no line items means the student is owed money
        expected = Decimal("-50.00")
        actual = self.controller.amount_owed()

        # WHY assertEqual not assertAlmostEqual:
        # assertAlmostEqual(a, b, places=2) would mask a Decimal vs float
        # mismatch. We want strict equality — financial amounts must be exact.
        self.assertEqual(
            actual,
            expected,
            msg=(
                f"Expected amount_owed={expected} after granting {aid_amount} "
                f"in aid, but got {actual}. Check for float contamination in "
                f"the controller's aid application logic."
            ),
        )

    def test_partial_grant_with_outstanding_line_item(self):
        """
        Adding a $100 line item then granting $40 aid should leave
        amount_owed() == $60.

        WHY this compound test:
        Real registrations have multiple line items (program cost, t-shirt,
        lunch, etc.) plus partial aid grants. This test verifies that the
        controller correctly nets them: sum(line_items) - sum(aid) = balance.

        $100.00 (line item) - $40.00 (aid) = $60.00 owed
        """
        line_item_amount = Decimal("100.00")
        aid_amount = Decimal("40.00")

        # Add the line item first (simulates program registration cost)
        self.controller.add_line_item(
            amount=line_item_amount,
            description="Program registration fee",
        )

        # Then apply partial financial aid
        self.controller.grant_financial_aid(aid_amount)

        expected = Decimal("60.00")
        actual = self.controller.amount_owed()

        self.assertEqual(
            actual,
            expected,
            msg=(
                f"Expected amount_owed={expected} after ${line_item_amount} "
                f"line item and ${aid_amount} aid grant, but got {actual}. "
                f"Verify that add_line_item and grant_financial_aid both use "
                f"Decimal arithmetic and that amount_owed() sums them correctly."
            ),
        )

    def test_amount_owed_is_zero_with_no_transactions(self):
        """
        Edge case: a fresh controller with no line items or aid should
        return Decimal('0.00'), not 0 (int) or 0.0 (float).

        WHY type-check the return value:
        If amount_owed() returns int(0) instead of Decimal('0.00'), code
        that does `total += controller.amount_owed()` will silently convert
        a Decimal accumulator to a float, introducing the exact precision
        bugs we're trying to prevent.
        """
        result = self.controller.amount_owed()

        self.assertEqual(result, Decimal("0.00"))
        self.assertIsInstance(
            result,
            Decimal,
            msg=(
                "amount_owed() must return a Decimal, not int or float. "
                "Mixing numeric types in financial summations causes "
                "IEEE 754 precision loss."
            ),
        )
