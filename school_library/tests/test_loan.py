from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestLibraryLoan(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Book = cls.env["school.library.book"]
        cls.Copy = cls.env["school.library.book.copy"]
        cls.Loan = cls.env["school.library.loan"]
        cls.Partner = cls.env["res.partner"]

        cls.borrower = cls.Partner.create({"name": "Loan Test Borrower", "is_student": True})
        cls.book = cls.Book.create({"title": "Loan Test Book"})
        cls.copy = cls.Copy.create({"book_id": cls.book.id, "barcode": "LOAN-001"})

    def _make_loan(self, **overrides):
        defaults = {
            "book_copy_id": self.copy.id,
            "borrower_id": self.borrower.id,
            "borrow_date": date(2099, 8, 1),
            "due_date": date(2099, 8, 15),
        }
        defaults.update(overrides)
        return self.Loan.create(defaults)

    def test_confirm_sets_copy_to_borrowed(self):
        loan = self._make_loan()
        loan.action_confirm()
        self.assertEqual(loan.state, "borrowed")
        self.assertEqual(self.copy.state, "borrowed")

    def test_cannot_borrow_unavailable_copy(self):
        self.copy.state = "lost"
        loan = self._make_loan()
        with self.assertRaises(UserError):
            loan.action_confirm()

    def test_return_on_time(self):
        # Use recent-past dates so `today` (test run time) is >= borrow_date,
        # satisfying the return_date >= borrow_date constraint.
        today = fields_context_today(self.env)
        loan = self._make_loan(
            borrow_date=today - timedelta(days=2),
            due_date=today + timedelta(days=12),
        )
        loan.action_confirm()
        loan.action_return()
        self.assertEqual(loan.state, "returned")
        self.assertEqual(self.copy.state, "available")

    def test_dates_constraint(self):
        with self.assertRaises(ValidationError):
            self._make_loan(due_date=date(2099, 7, 1))  # before borrow_date

    def test_cannot_double_borrow_copy(self):
        loan_a = self._make_loan()
        loan_a.action_confirm()
        loan_b = self.Loan.create(
            {
                "book_copy_id": self.copy.id,
                "borrower_id": self.borrower.id,
                "borrow_date": date(2099, 8, 2),
                "due_date": date(2099, 8, 16),
            }
        )
        # The second action_confirm should raise UserError because the copy
        # is no longer available (it was flipped to "borrowed" by loan_a).
        with self.assertRaises(UserError):
            loan_b.action_confirm()

    def test_fine_accrues_when_returned_late(self):
        # Use dates in the past so "today" is after due and the state is
        # computed consistently regardless of when the test runs.
        today = fields_context_today(self.env)
        loan = self._make_loan(
            borrow_date=today - timedelta(days=30),
            due_date=today - timedelta(days=20),
        )
        loan.action_confirm()
        # Pretend the student returns today (still 20 days late).
        loan.action_return()
        loan.invalidate_recordset(["is_overdue", "overdue_days", "fine_amount"])
        self.assertEqual(loan.state, "returned_late")
        self.assertEqual(loan.overdue_days, 20)
        self.assertAlmostEqual(loan.fine_amount, 20 * 5.0, places=2)

    def test_mark_lost_from_borrowed(self):
        loan = self._make_loan()
        loan.action_confirm()
        loan.action_mark_lost()
        self.assertEqual(loan.state, "lost")
        self.assertEqual(self.copy.state, "lost")

    def test_config_rate_read(self):
        self.env["ir.config_parameter"].sudo().set_param("school_library.fine_per_day", "10.0")
        self.assertEqual(self.Loan._get_fine_per_day(), 10.0)

    def test_config_period_read(self):
        self.env["ir.config_parameter"].sudo().set_param("school_library.loan_period_days", "7")
        self.assertEqual(self.Loan._get_loan_period_days(), 7)


def fields_context_today(env):
    from odoo import fields

    return fields.Date.context_today(env.user)
