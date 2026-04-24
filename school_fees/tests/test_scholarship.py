from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestScholarship(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.Structure = cls.env["school.fee.structure"]
        cls.Line = cls.env["school.fee.structure.line"]
        cls.Enrollment = cls.env["school.fee.enrollment"]
        cls.Scholarship = cls.env["school.scholarship"]
        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        Partner = cls.env["res.partner"]
        Classroom = cls.env["school.classroom"]

        cls.year = Year.create(
            {
                "name": "Sch 2099",
                "code": "SC99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "Sch Term",
                "code": "SCT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.classroom = Classroom.create(
            {"name": "Sch Room", "code": "SCR", "grade_level": "9", "academic_year_id": cls.year.id}
        )
        cls.student = Partner.create(
            {"name": "Sch Student", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.product = cls.Product.create(
            {"name": "Sch Tuition", "type": "service", "is_school_fee": True, "list_price": 10000.0}
        )
        cls.structure = cls.Structure.create(
            {"code": "SCH-STRUCT", "grade_level": "9", "term_id": cls.term.id, "state": "open"}
        )
        cls.Line.create(
            {"structure_id": cls.structure.id, "product_id": cls.product.id, "quantity": 1, "price_unit": 10000}
        )
        cls.enrollment = cls.Enrollment.create({"student_id": cls.student.id, "structure_id": cls.structure.id})

    def test_percentage_type(self):
        s = self.Scholarship.create(
            {
                "name": "10%",
                "enrollment_id": self.enrollment.id,
                "discount_type": "percentage",
                "discount_percentage": 10.0,
            }
        )
        self.assertAlmostEqual(s.computed_amount, 1000.0, places=2)

    def test_amount_type(self):
        s = self.Scholarship.create(
            {
                "name": "500 off",
                "enrollment_id": self.enrollment.id,
                "discount_type": "amount",
                "discount_amount": 500.0,
            }
        )
        self.assertAlmostEqual(s.computed_amount, 500.0, places=2)

    def test_percentage_must_not_set_amount(self):
        with self.assertRaises(ValidationError):
            self.Scholarship.create(
                {
                    "name": "Bad",
                    "enrollment_id": self.enrollment.id,
                    "discount_type": "percentage",
                    "discount_percentage": 5.0,
                    "discount_amount": 100.0,
                }
            )

    def test_amount_must_not_set_percentage(self):
        with self.assertRaises(ValidationError):
            self.Scholarship.create(
                {
                    "name": "Bad",
                    "enrollment_id": self.enrollment.id,
                    "discount_type": "amount",
                    "discount_amount": 100.0,
                    "discount_percentage": 5.0,
                }
            )

    def test_percentage_out_of_range(self):
        with self.assertRaises(ValidationError):
            self.Scholarship.create(
                {
                    "name": "Bad",
                    "enrollment_id": self.enrollment.id,
                    "discount_type": "percentage",
                    "discount_percentage": 150.0,
                }
            )

    def test_amount_zero_rejected(self):
        with self.assertRaises(ValidationError):
            self.Scholarship.create(
                {
                    "name": "Zero",
                    "enrollment_id": self.enrollment.id,
                    "discount_type": "amount",
                    "discount_amount": 0.0,
                }
            )

    def test_state_transitions(self):
        s = self.Scholarship.create(
            {
                "name": "Lifecycle",
                "enrollment_id": self.enrollment.id,
                "discount_type": "percentage",
                "discount_percentage": 5.0,
            }
        )
        self.assertEqual(s.state, "draft")
        s.action_apply()
        self.assertEqual(s.state, "applied")
        s.action_revoke()
        self.assertEqual(s.state, "revoked")
