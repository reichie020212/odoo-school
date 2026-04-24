import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestTeacherEmployee(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env["hr.employee"]

    def test_create_teacher(self):
        teacher = self.Employee.create(
            {
                "name": "Jane Doe",
                "is_teacher": True,
                "teacher_employee_number": "T-TEST-0001",
                "teacher_qualifications": "BSc, MEd.",
            }
        )
        self.assertTrue(teacher.is_teacher)
        self.assertEqual(teacher.teacher_employee_number, "T-TEST-0001")

    def test_non_teacher_has_no_teacher_number(self):
        staff = self.Employee.create({"name": "Maintenance Guy"})
        self.assertFalse(staff.is_teacher)
        self.assertFalse(staff.teacher_employee_number)

    @mute_logger("odoo.sql_db")
    def test_teacher_number_unique(self):
        self.Employee.create({"name": "A", "is_teacher": True, "teacher_employee_number": "T-DUP"})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Employee.create(
                {
                    "name": "B",
                    "is_teacher": True,
                    "teacher_employee_number": "T-DUP",
                }
            )
            self.env.flush_all()

    def test_teacher_filter_excludes_staff(self):
        self.Employee.create({"name": "Teacher A", "is_teacher": True})
        self.Employee.create({"name": "Janitor", "is_teacher": False})
        teachers = self.Employee.search([("is_teacher", "=", True)])
        names = teachers.mapped("name")
        self.assertIn("Teacher A", names)
        self.assertNotIn("Janitor", names)
