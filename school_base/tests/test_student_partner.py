from datetime import date, timedelta

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestStudentPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]

    def test_admission_number_auto_generated(self):
        student = self.Partner.create({"name": "Auto Student", "is_student": True})
        self.assertTrue(student.student_admission_number)

    def test_admission_numbers_are_unique(self):
        student_a = self.Partner.create({"name": "Student A", "is_student": True})
        student_b = self.Partner.create({"name": "Student B", "is_student": True})
        self.assertNotEqual(
            student_a.student_admission_number,
            student_b.student_admission_number,
        )

    @mute_logger("odoo.sql_db")
    def test_admission_number_unique_constraint(self):
        student_a = self.Partner.create({"name": "Student A", "is_student": True})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Partner.create(
                {
                    "name": "Student B",
                    "is_student": True,
                    "student_admission_number": student_a.student_admission_number,
                }
            )
            self.env.flush_all()

    def test_non_student_has_no_admission_number(self):
        vendor = self.Partner.create({"name": "Some Vendor", "is_student": False})
        self.assertFalse(vendor.student_admission_number)

    def test_guardian_ward_symmetric(self):
        guardian = self.Partner.create({"name": "Guardian", "is_guardian": True})
        student = self.Partner.create(
            {
                "name": "Student",
                "is_student": True,
                "student_guardian_ids": [(6, 0, [guardian.id])],
            }
        )
        # Assigning guardian on student should populate ward on guardian
        guardian.invalidate_recordset(["student_ward_ids"])
        self.assertIn(student, guardian.student_ward_ids)

    def test_cannot_be_own_guardian(self):
        student = self.Partner.create({"name": "Loner", "is_student": True, "is_guardian": True})
        with self.assertRaises(ValidationError):
            student.write({"student_guardian_ids": [(6, 0, [student.id])]})

    def test_dob_must_be_past(self):
        future = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.Partner.create(
                {
                    "name": "Future Student",
                    "is_student": True,
                    "student_date_of_birth": future,
                }
            )

    def test_promote_partner_to_student_generates_number(self):
        partner = self.Partner.create({"name": "Not Yet", "is_student": False})
        self.assertFalse(partner.student_admission_number)
        partner.write({"is_student": True})
        self.assertTrue(partner.student_admission_number)
