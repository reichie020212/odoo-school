from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSessionMaterialize(TransactionCase):
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
                "name": "Mat Test 2099",
                "code": "MT99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        # Term covers exactly Mon 2099-08-03 through Sun 2099-08-16 → 2 Mondays, 2 Wednesdays.
        cls.term = cls.Term.create(
            {
                "name": "Mat Term",
                "code": "MTT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 3),
                "date_end": date(2099, 8, 16),
            }
        )
        cls.teacher = cls.Employee.create({"name": "Mat Teacher", "is_teacher": True})
        cls.classroom = cls.Classroom.create(
            {
                "name": "Mat Classroom",
                "code": "MAT",
                "grade_level": "10",
                "academic_year_id": cls.year.id,
            }
        )
        cls.subject = cls.Subject.create({"name": "Mat Subject", "code": "MAT-S"})

        cls.course = cls.Course.create(
            {
                "subject_id": cls.subject.id,
                "term_id": cls.term.id,
                "classroom_id": cls.classroom.id,
                "teacher_id": cls.teacher.id,
            }
        )
        cls.env["school.course.schedule.rule"].create(
            [
                {
                    "course_id": cls.course.id,
                    "weekday": "mon",
                    "time_start": 8.0,
                    "duration": 1.0,
                },
                {
                    "course_id": cls.course.id,
                    "weekday": "wed",
                    "time_start": 9.0,
                    "duration": 1.5,
                },
            ]
        )

    def test_materialize_creates_expected_sessions(self):
        self.course.action_materialize_sessions()
        # 2 Mondays (3rd, 10th) + 2 Wednesdays (5th, 12th) = 4 sessions.
        self.assertEqual(self.course.session_count, 4)
        weekdays = sorted(ev.start.weekday() for ev in self.course.session_ids)
        # Monday=0, Wednesday=2
        self.assertEqual(weekdays, [0, 0, 2, 2])

    def test_materialize_is_idempotent(self):
        self.course.action_materialize_sessions()
        initial = self.course.session_count
        with self.assertRaises(UserError):
            # All dates already materialised — should raise "no new sessions".
            self.course.action_materialize_sessions()
        self.assertEqual(self.course.session_count, initial)

    def test_materialize_requires_schedule_rule(self):
        self.course.schedule_rule_ids.unlink()
        with self.assertRaises(UserError):
            self.course.action_materialize_sessions()

    def test_session_duration(self):
        self.course.action_materialize_sessions()
        for ev in self.course.session_ids:
            if ev.start.weekday() == 0:  # Monday
                self.assertEqual(ev.duration, 1.0)
            elif ev.start.weekday() == 2:  # Wednesday
                self.assertEqual(ev.duration, 1.5)
