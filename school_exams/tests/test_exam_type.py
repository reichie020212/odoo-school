import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestExamType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ExamType = cls.env["school.exam.type"]

    def test_create(self):
        et = self.ExamType.create({"name": "Pop Quiz", "code": "PQ"})
        self.assertEqual(et.default_weight, 25.0)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self.ExamType.create({"name": "Lab Report", "code": "LAB"})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.ExamType.create({"name": "Lab Report 2", "code": "LAB"})
            self.env.flush_all()
