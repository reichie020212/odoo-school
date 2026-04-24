import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestGradingScale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Scale = cls.env["school.grading.scale"]
        cls.Band = cls.env["school.grading.scale.band"]
        # Archive the demo default so our tests own the "single default" invariant.
        cls.Scale.search([("is_default", "=", True)]).write({"is_default": False})

    def _make_scale(self, **overrides):
        defaults = {"name": "Test Scale", "code": "TST"}
        defaults.update(overrides)
        return self.Scale.create(defaults)

    def test_create_scale(self):
        scale = self._make_scale()
        self.assertEqual(scale.code, "TST")
        self.assertFalse(scale.is_default)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self._make_scale()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_scale()
            self.env.flush_all()

    def test_only_one_default(self):
        first = self._make_scale(code="D1", is_default=True)
        self.assertTrue(first.is_default)
        with self.assertRaises(ValidationError):
            self._make_scale(code="D2", is_default=True)

    def test_band_lookup_returns_highest_matching(self):
        scale = self._make_scale()
        self.Band.create(
            [
                {"scale_id": scale.id, "letter": "A", "min_percentage": 90, "gpa_value": 4.0},
                {"scale_id": scale.id, "letter": "B", "min_percentage": 80, "gpa_value": 3.0},
                {"scale_id": scale.id, "letter": "C", "min_percentage": 70, "gpa_value": 2.0},
                {"scale_id": scale.id, "letter": "F", "min_percentage": 0, "gpa_value": 0.0},
            ]
        )
        self.assertEqual(scale.band_for_percentage(95.0).letter, "A")
        self.assertEqual(scale.band_for_percentage(90.0).letter, "A")
        self.assertEqual(scale.band_for_percentage(89.99).letter, "B")
        self.assertEqual(scale.band_for_percentage(74.0).letter, "C")
        self.assertEqual(scale.band_for_percentage(0.0).letter, "F")
        self.assertEqual(scale.band_for_percentage(-5.0).letter, "F")

    def test_get_default_scale_returns_default(self):
        default = self._make_scale(code="DEF", is_default=True)
        self.assertEqual(self.Scale.get_default_scale(), default)
