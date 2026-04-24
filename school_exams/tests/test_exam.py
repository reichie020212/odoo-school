from datetime import date

from odoo.tests.common import TransactionCase


class TestExam(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Exam = cls.env["school.exam"]
        cls.ExamType = cls.env["school.exam.type"]
        cls.Result = cls.env["school.exam.result"]

        # Reuse a helper set of academic records so we don't need demo data.
        Year = cls.env["school.academic.year"]
        Term = cls.env["school.academic.term"]
        Employee = cls.env["hr.employee"]
        Classroom = cls.env["school.classroom"]
        Course = cls.env["school.course"]
        Subject = cls.env["school.subject"]
        Partner = cls.env["res.partner"]

        cls.year = Year.create(
            {
                "name": "ExT 2099",
                "code": "EX99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = Term.create(
            {
                "name": "ExT Term",
                "code": "EXT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.teacher = Employee.create({"name": "Exam Teacher", "is_teacher": True})
        cls.classroom = Classroom.create(
            {"name": "Exam Room", "code": "EXR", "grade_level": "10", "academic_year_id": cls.year.id}
        )
        cls.student = Partner.create(
            {"name": "Exam Student", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.subject = Subject.create({"name": "Exam Subject", "code": "EXS"})
        cls.course = Course.create(
            {
                "subject_id": cls.subject.id,
                "term_id": cls.term.id,
                "classroom_id": cls.classroom.id,
                "teacher_id": cls.teacher.id,
            }
        )
        cls.exam_type = cls.ExamType.create({"name": "Test Quiz", "code": "TQ", "default_weight": 15.0})

    def _make_exam(self, **overrides):
        defaults = {
            "course_id": self.course.id,
            "exam_type_id": self.exam_type.id,
            "date": date(2099, 9, 1),
            "max_score": 100.0,
        }
        defaults.update(overrides)
        return self.Exam.create(defaults)

    def test_name_autocomputes(self):
        exam = self._make_exam()
        self.assertIn(self.exam_type.name, exam.name)
        self.assertIn(self.course.name, exam.name)

    def test_weight_seeded_from_type(self):
        exam = self._make_exam()
        self.assertEqual(exam.weight, self.exam_type.default_weight)

    def test_weight_explicit_overrides_default(self):
        exam = self._make_exam(weight=42.0)
        self.assertEqual(exam.weight, 42.0)

    def test_state_transitions(self):
        exam = self._make_exam()
        self.assertEqual(exam.state, "draft")
        exam.action_publish()
        self.assertEqual(exam.state, "published")
        exam.action_close()
        self.assertEqual(exam.state, "closed")

    def test_generate_placeholders_creates_rows(self):
        exam = self._make_exam()
        exam.action_generate_result_placeholders()
        self.assertEqual(exam.result_count, 1)
        self.assertEqual(exam.result_ids.student_id, self.student)
