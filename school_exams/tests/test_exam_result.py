from datetime import date

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestExamResult(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        Employee = cls.env["hr.employee"]
        Classroom = cls.env["school.classroom"]
        Course = cls.env["school.course"]
        Partner = cls.env["res.partner"]
        cls.Exam = cls.env["school.exam"]
        cls.ExamType = cls.env["school.exam.type"]
        cls.Result = cls.env["school.exam.result"]
        cls.Scale = cls.env["school.grading.scale"]
        cls.Band = cls.env["school.grading.scale.band"]

        # Swap the default scale so tests don't depend on demo data ordering.
        cls.Scale.search([("is_default", "=", True)]).write({"is_default": False})
        cls.scale = cls.Scale.create({"name": "Result Scale", "code": "RES", "is_default": True})
        cls.Band.create(
            [
                {"scale_id": cls.scale.id, "letter": "A", "min_percentage": 90, "gpa_value": 4.0},
                {"scale_id": cls.scale.id, "letter": "B", "min_percentage": 80, "gpa_value": 3.0},
                {"scale_id": cls.scale.id, "letter": "C", "min_percentage": 70, "gpa_value": 2.0},
                {"scale_id": cls.scale.id, "letter": "F", "min_percentage": 0, "gpa_value": 0.0},
            ]
        )

        cls.year = Year.create(
            {
                "name": "ExR 2099",
                "code": "ER99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "ER Term",
                "code": "ERT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.teacher = Employee.create({"name": "ER Teacher", "is_teacher": True})
        cls.classroom = Classroom.create(
            {"name": "ER Room", "code": "ERR", "grade_level": "10", "academic_year_id": cls.year.id}
        )
        cls.student_a = Partner.create(
            {"name": "ER Student A", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.student_b = Partner.create(
            {"name": "ER Student B", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.outsider = Partner.create({"name": "ER Outsider", "is_student": True})
        cls.subject = cls.env["school.subject"].create({"name": "ER Subject", "code": "ERS"})
        cls.course = Course.create(
            {
                "subject_id": cls.subject.id,
                "term_id": cls.term.id,
                "classroom_id": cls.classroom.id,
                "teacher_id": cls.teacher.id,
            }
        )
        cls.exam_type = cls.ExamType.create({"name": "ER Quiz", "code": "ERQ", "default_weight": 20.0})
        cls.exam = cls.Exam.create(
            {
                "course_id": cls.course.id,
                "exam_type_id": cls.exam_type.id,
                "date": date(2099, 9, 1),
                "max_score": 50.0,
                "state": "published",
            }
        )

    def test_create_result(self):
        r = self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": 45.0})
        self.assertEqual(r.percentage, 90.0)
        self.assertEqual(r.letter_grade, "A")
        self.assertEqual(r.gpa_value, 4.0)

    @mute_logger("odoo.sql_db")
    def test_unique_exam_student(self):
        self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": 40})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": 41})
            self.env.flush_all()

    def test_non_enrolled_student_rejected(self):
        with self.assertRaises(ValidationError):
            self.Result.create({"exam_id": self.exam.id, "student_id": self.outsider.id, "score": 30})

    def test_negative_score_rejected(self):
        with self.assertRaises(ValidationError):
            self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": -1})

    def test_over_max_rejected(self):
        with self.assertRaises(ValidationError):
            self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": 60})

    def test_percentage_recomputes_on_score_change(self):
        r = self.Result.create({"exam_id": self.exam.id, "student_id": self.student_a.id, "score": 25})
        self.assertEqual(r.percentage, 50.0)
        r.score = 50
        self.assertEqual(r.percentage, 100.0)
        self.assertEqual(r.letter_grade, "A")
