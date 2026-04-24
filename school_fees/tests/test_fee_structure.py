from datetime import date

import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestFeeStructure(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Structure = cls.env["school.fee.structure"]
        cls.Line = cls.env["school.fee.structure.line"]
        cls.Product = cls.env["product.product"]
        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        cls.year = Year.create(
            {
                "name": "FS 2099",
                "code": "FS99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "FS Term",
                "code": "FST",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.tuition = cls.Product.create(
            {"name": "Test Tuition", "type": "service", "is_school_fee": True, "list_price": 30000.0}
        )
        cls.lab = cls.Product.create(
            {"name": "Test Lab", "type": "service", "is_school_fee": True, "list_price": 3000.0}
        )

    def _make_structure(self, **overrides):
        defaults = {"code": "FST-TST", "grade_level": "9", "term_id": self.term.id}
        defaults.update(overrides)
        return self.Structure.create(defaults)

    def test_create_structure_autocomputes_name(self):
        s = self._make_structure()
        self.assertIn(self.term.code, s.name)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self._make_structure()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_structure(grade_level="10")
            self.env.flush_all()

    @mute_logger("odoo.sql_db")
    def test_grade_term_unique(self):
        self._make_structure()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_structure(code="FST-TST-2")
            self.env.flush_all()

    def test_total_rolls_up_from_lines(self):
        s = self._make_structure()
        self.Line.create(
            [
                {"structure_id": s.id, "product_id": self.tuition.id, "quantity": 1, "price_unit": 30000},
                {"structure_id": s.id, "product_id": self.lab.id, "quantity": 1, "price_unit": 3000},
            ]
        )
        s.invalidate_recordset(["total_amount"])
        self.assertAlmostEqual(s.total_amount, 33000.0, places=2)

    def test_line_subtotal_multiplies(self):
        s = self._make_structure()
        line = self.Line.create({"structure_id": s.id, "product_id": self.lab.id, "quantity": 2, "price_unit": 1500})
        self.assertAlmostEqual(line.subtotal, 3000.0, places=2)
