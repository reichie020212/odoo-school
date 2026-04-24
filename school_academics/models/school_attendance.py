from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolAttendance(models.Model):
    _name = "school.attendance"
    _description = "Student Attendance"
    _order = "session_id desc, student_id"
    _rec_name = "student_id"

    student_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_student", "=", True)],
        index=True,
        ondelete="restrict",
    )
    session_id = fields.Many2one(
        "calendar.event",
        required=True,
        ondelete="cascade",
        index=True,
        string="Session",
    )
    course_id = fields.Many2one(
        "school.course",
        related="session_id.school_course_id",
        store=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
        ],
        default="present",
        required=True,
    )
    note = fields.Char()
    recorded_by_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        required=True,
    )
    recorded_at = fields.Datetime(default=fields.Datetime.now, required=True)

    _attendance_student_session_unique = models.Constraint(
        "UNIQUE(student_id, session_id)",
        "A student can only have one attendance record per session.",
    )

    @api.constrains("student_id", "session_id")
    def _check_student_enrolled(self):
        for rec in self:
            course = rec.session_id.school_course_id
            if not course:
                raise ValidationError(_("Attendance can only be recorded against sessions linked to a school course."))
            if rec.student_id not in course.student_ids:
                raise ValidationError(
                    _("Student %(student)s is not enrolled in course %(course)s.")
                    % {"student": rec.student_id.display_name, "course": course.display_name}
                )
