from datetime import date

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAcademicYear(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Year = cls.env["school.academic.year"]
        cls.Term = cls.env["school.academic.term"]
        # Archive any existing active years so we start from a known state.
        cls.Year.search([("state", "=", "active")]).write({"state": "archived"})

    def _make_year(self, **overrides):
        defaults = {
            "name": "Test 2099–2100",
            "code": "TEST99",
            "date_start": date(2099, 8, 1),
            "date_end": date(2100, 5, 31),
        }
        defaults.update(overrides)
        return self.Year.create(defaults)

    def test_create_year(self):
        year = self._make_year()
        self.assertEqual(year.state, "draft")
        self.assertFalse(year.is_current)

    def test_end_after_start(self):
        with self.assertRaises(ValidationError):
            self._make_year(date_end=date(2099, 1, 1))

    def test_only_one_active_year(self):
        first = self._make_year(code="TEST98")
        first.action_activate()
        second = self._make_year(code="TEST99B")
        with self.assertRaises(ValidationError):
            second.action_activate()

    @mute_logger("odoo.sql_db")
    def test_unique_code(self):
        self._make_year(code="DUP1")
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_year(code="DUP1")
            self.env.flush_all()

    def test_term_within_year(self):
        year = self._make_year()
        # Term starting before year is rejected
        with self.assertRaises(ValidationError):
            self.Term.create(
                {
                    "name": "Before",
                    "code": "B",
                    "academic_year_id": year.id,
                    "date_start": date(2099, 7, 1),
                    "date_end": date(2099, 9, 30),
                }
            )

    def test_terms_no_overlap(self):
        year = self._make_year()
        self.Term.create(
            {
                "name": "S1",
                "code": "S1",
                "academic_year_id": year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 20),
            }
        )
        with self.assertRaises(ValidationError):
            self.Term.create(
                {
                    "name": "S1-overlap",
                    "code": "S1X",
                    "academic_year_id": year.id,
                    "date_start": date(2099, 12, 1),  # overlaps S1
                    "date_end": date(2100, 3, 1),
                }
            )

    @mute_logger("odoo.sql_db")
    def test_term_code_unique_per_year(self):
        year = self._make_year()
        self.Term.create(
            {
                "name": "S1",
                "code": "S1",
                "academic_year_id": year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 20),
            }
        )
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Term.create(
                {
                    "name": "S1 dup",
                    "code": "S1",
                    "academic_year_id": year.id,
                    "date_start": date(2100, 1, 5),
                    "date_end": date(2100, 5, 31),
                }
            )
            self.env.flush_all()

    def test_is_current_computed(self):
        year = self._make_year(
            date_start=date.today().replace(month=1, day=1),
            date_end=date.today().replace(month=12, day=31),
            code="CUR99",
        )
        year.action_activate()
        self.assertTrue(year.is_current)
