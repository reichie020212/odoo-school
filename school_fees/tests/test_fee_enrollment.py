from datetime import date

import psycopg2
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestFeeEnrollment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]
        cls.Structure = cls.env["school.fee.structure"]
        cls.Line = cls.env["school.fee.structure.line"]
        cls.Enrollment = cls.env["school.fee.enrollment"]
        cls.Scholarship = cls.env["school.scholarship"]
        cls.Move = cls.env["account.move"]
        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        Classroom = cls.env["school.classroom"]
        Partner = cls.env["res.partner"]

        cls.year = Year.create(
            {
                "name": "Enr 2099",
                "code": "EN99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "Enr Term",
                "code": "ENT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.classroom_g9 = Classroom.create(
            {"name": "G9 Room", "code": "G9R", "grade_level": "9", "academic_year_id": cls.year.id}
        )
        cls.classroom_g10 = Classroom.create(
            {"name": "G10 Room", "code": "G10R", "grade_level": "10", "academic_year_id": cls.year.id}
        )
        cls.guardian = Partner.create({"name": "Enr Guardian", "is_guardian": True})
        cls.student_g9 = Partner.create(
            {
                "name": "G9 Student",
                "is_student": True,
                "student_classroom_id": cls.classroom_g9.id,
                "student_guardian_ids": [(6, 0, [cls.guardian.id])],
            }
        )
        cls.student_g10 = Partner.create(
            {"name": "G10 Student", "is_student": True, "student_classroom_id": cls.classroom_g10.id}
        )

        cls.product_tuition = cls.Product.create(
            {"name": "Enr Tuition", "type": "service", "is_school_fee": True, "list_price": 20000.0}
        )
        cls.product_lab = cls.Product.create(
            {"name": "Enr Lab", "type": "service", "is_school_fee": True, "list_price": 3000.0}
        )

        cls.structure_g9 = cls.Structure.create(
            {"code": "ENR-G9", "grade_level": "9", "term_id": cls.term.id, "state": "open"}
        )
        cls.Line.create(
            [
                {
                    "structure_id": cls.structure_g9.id,
                    "product_id": cls.product_tuition.id,
                    "quantity": 1,
                    "price_unit": 20000,
                },
                {
                    "structure_id": cls.structure_g9.id,
                    "product_id": cls.product_lab.id,
                    "quantity": 1,
                    "price_unit": 3000,
                },
            ]
        )

    def _make_enrollment(self, student=None, structure=None):
        return self.Enrollment.create(
            {
                "student_id": (student or self.student_g9).id,
                "structure_id": (structure or self.structure_g9).id,
            }
        )

    def test_create_enrollment_totals(self):
        enrollment = self._make_enrollment()
        self.assertAlmostEqual(enrollment.structure_total, 23000.0, places=2)
        self.assertAlmostEqual(enrollment.amount_total, 23000.0, places=2)
        self.assertAlmostEqual(enrollment.amount_due, 23000.0, places=2)

    @mute_logger("odoo.sql_db")
    def test_unique_student_structure(self):
        self._make_enrollment()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_enrollment()
            self.env.flush_all()

    def test_grade_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_enrollment(student=self.student_g10)

    def test_generate_invoice_creates_account_move(self):
        enrollment = self._make_enrollment()
        enrollment.action_generate_invoice()
        self.assertTrue(enrollment.invoice_id)
        self.assertEqual(enrollment.invoice_id.move_type, "out_invoice")
        self.assertEqual(enrollment.invoice_id.partner_id, self.student_g9)
        self.assertEqual(len(enrollment.invoice_id.invoice_line_ids), 2)
        self.assertAlmostEqual(enrollment.invoice_id.amount_untaxed, 23000.0, places=2)
        self.assertEqual(enrollment.state, "invoiced")

    def test_scholarship_applied_creates_negative_line(self):
        enrollment = self._make_enrollment()
        self.Scholarship.create(
            {
                "name": "Enr 10%",
                "enrollment_id": enrollment.id,
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "state": "applied",
            }
        )
        enrollment.invalidate_recordset(["scholarship_total", "amount_total"])
        self.assertAlmostEqual(enrollment.scholarship_total, 2300.0, places=2)
        self.assertAlmostEqual(enrollment.amount_total, 20700.0, places=2)
        enrollment.action_generate_invoice()
        negative_lines = enrollment.invoice_id.invoice_line_ids.filtered(lambda line: line.price_unit < 0)
        self.assertEqual(len(negative_lines), 1)
        self.assertAlmostEqual(negative_lines.price_unit, -2300.0, places=2)

    def test_cannot_invoice_twice(self):
        enrollment = self._make_enrollment()
        enrollment.action_generate_invoice()
        with self.assertRaises(UserError):
            enrollment.action_generate_invoice()

    def test_cancel_clears_draft_invoice(self):
        enrollment = self._make_enrollment()
        enrollment.action_generate_invoice()
        invoice = enrollment.invoice_id
        self.assertEqual(invoice.state, "draft")
        enrollment.action_cancel()
        self.assertEqual(enrollment.state, "cancelled")
        self.assertEqual(invoice.state, "cancel")

    def test_guardians_subscribed_to_invoice(self):
        enrollment = self._make_enrollment()
        enrollment.action_generate_invoice()
        followers = enrollment.invoice_id.message_partner_ids
        self.assertIn(self.guardian, followers)

    def test_state_transitions(self):
        enrollment = self._make_enrollment()
        self.assertEqual(enrollment.state, "draft")
        enrollment.action_confirm()
        self.assertEqual(enrollment.state, "confirmed")
        enrollment.action_generate_invoice()
        self.assertEqual(enrollment.state, "invoiced")
