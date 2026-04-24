from datetime import date

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestClassroom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Year = cls.env["school.academic.year"]
        cls.Classroom = cls.env["school.classroom"]
        cls.Partner = cls.env["res.partner"]
        cls.Employee = cls.env["hr.employee"]

        cls.year = cls.Year.create(
            {
                "name": "Test 2099–2100",
                "code": "CLS99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )

    def _make_classroom(self, **overrides):
        defaults = {
            "name": "Grade 9 — A",
            "code": "9A",
            "grade_level": "9",
            "academic_year_id": self.year.id,
            "capacity": 30,
        }
        defaults.update(overrides)
        return self.Classroom.create(defaults)

    def test_create_classroom(self):
        room = self._make_classroom()
        self.assertEqual(room.student_count, 0)

    @mute_logger("odoo.sql_db")
    def test_classroom_code_unique_per_year(self):
        self._make_classroom()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_classroom()
            self.env.flush_all()

    def test_student_count_updates(self):
        room = self._make_classroom()
        self.Partner.create(
            {
                "name": "Alice Example",
                "is_student": True,
                "student_classroom_id": room.id,
            }
        )
        room.invalidate_recordset(["student_count"])
        self.assertEqual(room.student_count, 1)

    def test_capacity_hard_constraint(self):
        room = self._make_classroom(capacity=1)
        self.Partner.create(
            {
                "name": "First Student",
                "is_student": True,
                "student_classroom_id": room.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.Partner.create(
                {
                    "name": "Second Student",
                    "is_student": True,
                    "student_classroom_id": room.id,
                }
            )

    def test_homeroom_must_be_teacher(self):
        non_teacher = self.Employee.create({"name": "Some Admin", "is_teacher": False})
        with self.assertRaises(ValidationError):
            self._make_classroom(homeroom_teacher_id=non_teacher.id)

    def test_homeroom_teacher_ok(self):
        teacher = self.Employee.create({"name": "Teacher X", "is_teacher": True})
        room = self._make_classroom(homeroom_teacher_id=teacher.id)
        self.assertIn(room, teacher.teacher_homeroom_ids)
