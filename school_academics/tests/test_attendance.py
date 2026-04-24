from datetime import date, datetime

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSchoolAttendance(TransactionCase):
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
        cls.CalendarEvent = cls.env["calendar.event"]
        cls.Attendance = cls.env["school.attendance"]

        cls.year = cls.Year.create(
            {
                "name": "Att Test 2099",
                "code": "AT99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.term = cls.Term.create(
            {
                "name": "Att Term",
                "code": "ATT",
                "academic_year_id": cls.year.id,
                "date_start": date(2099, 8, 1),
                "date_end": date(2099, 12, 31),
            }
        )
        cls.teacher = cls.Employee.create({"name": "Att Teacher", "is_teacher": True})
        cls.classroom = cls.Classroom.create(
            {
                "name": "Att Classroom",
                "code": "ATC",
                "grade_level": "10",
                "academic_year_id": cls.year.id,
            }
        )
        cls.subject = cls.Subject.create({"name": "Att Subject", "code": "ATT-S"})
        cls.student_a = cls.Partner.create(
            {"name": "Att Student A", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.student_b = cls.Partner.create(
            {"name": "Att Student B", "is_student": True, "student_classroom_id": cls.classroom.id}
        )
        cls.outsider = cls.Partner.create({"name": "Att Outsider", "is_student": True})

        cls.course = cls.Course.create(
            {
                "subject_id": cls.subject.id,
                "term_id": cls.term.id,
                "classroom_id": cls.classroom.id,
                "teacher_id": cls.teacher.id,
            }
        )
        cls.session = cls.CalendarEvent.create(
            {
                "name": "Att Session",
                "start": datetime(2099, 8, 3, 8, 0, 0),
                "stop": datetime(2099, 8, 3, 9, 0, 0),
                "duration": 1.0,
                "school_course_id": cls.course.id,
            }
        )

    def test_create_attendance(self):
        att = self.Attendance.create(
            {
                "student_id": self.student_a.id,
                "session_id": self.session.id,
                "state": "present",
            }
        )
        self.assertEqual(att.course_id, self.course)
        self.assertTrue(att.recorded_at)

    @mute_logger("odoo.sql_db")
    def test_unique_student_session(self):
        self.Attendance.create(
            {
                "student_id": self.student_a.id,
                "session_id": self.session.id,
                "state": "present",
            }
        )
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Attendance.create(
                {
                    "student_id": self.student_a.id,
                    "session_id": self.session.id,
                    "state": "absent",
                }
            )
            self.env.flush_all()

    def test_non_enrolled_student_rejected(self):
        with self.assertRaises(ValidationError):
            self.Attendance.create(
                {
                    "student_id": self.outsider.id,
                    "session_id": self.session.id,
                    "state": "present",
                }
            )

    def test_session_without_course_rejected(self):
        non_school_event = self.CalendarEvent.create(
            {
                "name": "Random Meeting",
                "start": datetime(2099, 8, 3, 10, 0, 0),
                "stop": datetime(2099, 8, 3, 11, 0, 0),
                "duration": 1.0,
            }
        )
        with self.assertRaises(ValidationError):
            self.Attendance.create(
                {
                    "student_id": self.student_a.id,
                    "session_id": non_school_event.id,
                    "state": "present",
                }
            )

    def test_mark_all_present(self):
        self.session.action_school_mark_all_present()
        self.assertEqual(self.session.school_attendance_count, 2)
        self.assertEqual(self.session.school_present_count, 2)
        self.assertEqual(self.session.school_session_state, "completed")
        students = self.session.school_attendance_ids.mapped("student_id")
        self.assertIn(self.student_a, students)
        self.assertIn(self.student_b, students)

    def test_mark_all_present_is_additive(self):
        self.Attendance.create(
            {
                "student_id": self.student_a.id,
                "session_id": self.session.id,
                "state": "absent",
            }
        )
        self.session.action_school_mark_all_present()
        # Existing absent record should not be overwritten.
        records = self.session.school_attendance_ids
        self.assertEqual(len(records), 2)
        student_a_rec = records.filtered(lambda a: a.student_id == self.student_a)
        self.assertEqual(student_a_rec.state, "absent")
