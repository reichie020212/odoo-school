from datetime import date

import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestReportCard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Scale = cls.env["school.grading.scale"]
        cls.Band = cls.env["school.grading.scale.band"]
        cls.ExamType = cls.env["school.exam.type"]
        cls.Exam = cls.env["school.exam"]
        cls.Result = cls.env["school.exam.result"]
        cls.Card = cls.env["school.report.card"]
        cls.Line = cls.env["school.report.card.line"]

        # Own the "default scale" invariant.
        cls.Scale.search([("is_default", "=", True)]).write({"is_default": False})
        cls.scale = cls.Scale.create({"name": "RC Scale", "code": "RCS", "is_default": True})
        cls.Band.create(
            [
                {"scale_id": cls.scale.id, "letter": "A", "min_percentage": 90, "gpa_value": 4.0},
                {"scale_id": cls.scale.id, "letter": "B", "min_percentage": 80, "gpa_value": 3.0},
                {"scale_id": cls.scale.id, "letter": "C", "min_percentage": 70, "gpa_value": 2.0},
                {"scale_id": cls.scale.id, "letter": "F", "min_percentage": 0, "gpa_value": 0.0},
            ]
        )

        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        Employee = cls.env["hr.employee"]
        Classroom = cls.env["school.classroom"]
        Course = cls.env["school.course"]
        Subject = cls.env["school.subject"]
        Partner = cls.env["res.partner"]

        cls.year = Year.create(
            {
                "name": "RC 2099",
                "code": "RC99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "RC Term",
                "code": "RCT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.teacher = Employee.create({"name": "RC Teacher", "is_teacher": True})
        cls.classroom = Classroom.create(
            {"name": "RC Room", "code": "RCR", "grade_level": "10", "academic_year_id": cls.year.id}
        )
        cls.student = Partner.create(
            {"name": "RC Student", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.subject = Subject.create({"name": "RC Subject", "code": "RCSJ"})
        cls.course = Course.create(
            {
                "subject_id": cls.subject.id,
                "term_id": cls.term.id,
                "classroom_id": cls.classroom.id,
                "teacher_id": cls.teacher.id,
            }
        )
        cls.quiz_type = cls.ExamType.create({"name": "RC Quiz", "code": "RCQ", "default_weight": 20.0})
        cls.mid_type = cls.ExamType.create({"name": "RC Midterm", "code": "RCM", "default_weight": 30.0})
        cls.quiz = cls.Exam.create(
            {
                "course_id": cls.course.id,
                "exam_type_id": cls.quiz_type.id,
                "date": date(2099, 9, 1),
                "max_score": 50.0,
                "weight": 20.0,
                "state": "published",
            }
        )
        cls.midterm = cls.Exam.create(
            {
                "course_id": cls.course.id,
                "exam_type_id": cls.mid_type.id,
                "date": date(2099, 10, 1),
                "max_score": 100.0,
                "weight": 30.0,
                "state": "published",
            }
        )
        cls.Result.create(
            [
                {"exam_id": cls.quiz.id, "student_id": cls.student.id, "score": 45},  # 90%
                {"exam_id": cls.midterm.id, "student_id": cls.student.id, "score": 87},  # 87%
            ]
        )

    def _make_card(self, **overrides):
        defaults = {"student_id": self.student.id, "term_id": self.term.id}
        defaults.update(overrides)
        return self.Card.create(defaults)

    def test_create_card(self):
        card = self._make_card()
        self.assertEqual(card.state, "draft")

    @mute_logger("odoo.sql_db")
    def test_unique_student_term(self):
        self._make_card()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_card()
            self.env.flush_all()

    def test_generate_lines_enumerates_student_courses(self):
        card = self._make_card()
        card.action_generate_lines()
        self.assertEqual(len(card.line_ids), 1)
        self.assertEqual(card.line_ids.course_id, self.course)

    def test_line_percentage_is_weighted_average(self):
        card = self._make_card()
        card.action_generate_lines()
        line = card.line_ids
        # (90 * 20 + 87 * 30) / (20 + 30) = 88.2
        self.assertAlmostEqual(line.percentage, 88.2, places=2)
        self.assertEqual(line.letter_grade, "B")
        self.assertEqual(line.gpa_value, 3.0)
        self.assertFalse(line.is_incomplete)

    def test_line_incomplete_when_no_graded_exams(self):
        # Revert exam state so they aren't counted as graded.
        (self.quiz | self.midterm).write({"state": "draft"})
        card = self._make_card()
        card.action_generate_lines()
        self.assertTrue(card.line_ids.is_incomplete)
        self.assertEqual(card.line_ids.percentage, 0.0)

    def test_overall_aggregates_from_lines(self):
        card = self._make_card()
        card.action_generate_lines()
        card.invalidate_recordset(["overall_percentage", "overall_gpa", "overall_letter"])
        self.assertAlmostEqual(card.overall_percentage, 88.2, places=2)
        self.assertEqual(card.overall_letter, "B")

    def test_state_lifecycle(self):
        card = self._make_card()
        card.action_generate_lines()
        card.action_finalize()
        self.assertEqual(card.state, "final")
        card.action_distribute()
        self.assertEqual(card.state, "distributed")
        card.action_reset_to_draft()
        self.assertEqual(card.state, "draft")
