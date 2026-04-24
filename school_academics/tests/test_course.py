from datetime import date

import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSchoolCourse(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Subject = cls.env["school.subject"]
        cls.Course = cls.env["school.course"]
        cls.Classroom = cls.env["school.classroom"]
        cls.Year = cls.env["school.academic.year"]
        cls.Term = cls.env["school.academic.term"]
        cls.Partner = cls.env["res.partner"]
        cls.Employee = cls.env["hr.employee"]

        cls.year = cls.Year.create(
            {
                "name": "Course Test 2099",
                "code": "CT99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = cls.Term.create(
            {
                "name": "CT99 Term",
                "code": "CTT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.teacher = cls.Employee.create({"name": "Course Test Teacher", "is_teacher": True})
        cls.classroom = cls.Classroom.create(
            {
                "name": "Course Test Classroom",
                "code": "CTC",
                "grade_level": "10",
                "academic_year_id": cls.year.id,
                "homeroom_teacher_id": cls.teacher.id,
            }
        )
        cls.subject = cls.Subject.create({"name": "Course Test Subject", "code": "CTS"})
        cls.student_a = cls.Partner.create(
            {"name": "Course Test Student A", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.student_b = cls.Partner.create(
            {"name": "Course Test Student B", "is_student": True, "student_classroom_id": cls.classroom.id}
        )

    def _make_course(self, **overrides):
        defaults = {
            "subject_id": self.subject.id,
            "term_id": self.term.id,
            "classroom_id": self.classroom.id,
            "teacher_id": self.teacher.id,
        }
        defaults.update(overrides)
        return self.Course.create(defaults)

    def test_create_course_auto_enrolls_classroom_roster(self):
        course = self._make_course()
        self.assertEqual(course.student_count, 2)
        self.assertIn(self.student_a, course.student_ids)
        self.assertIn(self.student_b, course.student_ids)

    def test_explicit_enrollment_overrides_auto(self):
        course = self._make_course(student_ids=[(6, 0, [self.student_a.id])])
        self.assertEqual(course.student_count, 1)
        self.assertIn(self.student_a, course.student_ids)

    def test_reset_enrollment_rehydrates_from_classroom(self):
        course = self._make_course()
        course.student_ids = [(5, 0, 0)]  # clear enrollment
        self.assertEqual(course.student_count, 0)
        course.action_reset_enrollment()
        self.assertEqual(course.student_count, 2)

    @mute_logger("odoo.sql_db")
    def test_unique_subject_classroom_term(self):
        self._make_course()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_course()
            self.env.flush_all()

    def test_name_autocomputes(self):
        course = self._make_course()
        self.assertIn(self.subject.name, course.name)
        self.assertIn(self.classroom.code, course.name)
        self.assertIn(self.term.code, course.name)

    def test_academic_year_related_from_term(self):
        course = self._make_course()
        self.assertEqual(course.academic_year_id, self.year)

    def test_state_transitions(self):
        course = self._make_course()
        self.assertEqual(course.state, "draft")
        course.action_open()
        self.assertEqual(course.state, "open")
        course.action_close()
        self.assertEqual(course.state, "closed")
        course.action_reset_to_draft()
        self.assertEqual(course.state, "draft")
