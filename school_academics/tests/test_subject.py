import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSchoolSubject(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Subject = cls.env["school.subject"]

    def test_create_subject(self):
        subject = self.Subject.create({"name": "Algebra I", "code": "MATH-9"})
        self.assertEqual(subject.name, "Algebra I")
        self.assertEqual(subject.default_weekly_hours, 3.0)
        self.assertEqual(subject.course_count, 0)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self.Subject.create({"name": "Physics", "code": "PHY-10"})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Subject.create({"name": "Duplicate Physics", "code": "PHY-10"})
            self.env.flush_all()

    def test_archive_flag(self):
        subject = self.Subject.create({"name": "Retired Subject", "code": "OLD-01"})
        subject.active = False
        # Searching without an active filter should not return archived records.
        self.assertFalse(self.Subject.search([("id", "=", subject.id)]))
        self.assertTrue(self.Subject.with_context(active_test=False).search([("id", "=", subject.id)]))
