from odoo import _, api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    school_course_id = fields.Many2one(
        "school.course",
        string="School Course",
        index=True,
        ondelete="set null",
        help="Marks this calendar event as a session of a school course.",
    )
    school_attendance_ids = fields.One2many(
        "school.attendance",
        "session_id",
        string="Attendance",
    )
    school_session_state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Session Status",
        default="scheduled",
    )
    school_attendance_count = fields.Integer(
        compute="_compute_school_attendance_counts",
        store=True,
    )
    school_present_count = fields.Integer(
        compute="_compute_school_attendance_counts",
        store=True,
    )

    @api.depends("school_attendance_ids", "school_attendance_ids.state")
    def _compute_school_attendance_counts(self):
        for rec in self:
            rec.school_attendance_count = len(rec.school_attendance_ids)
            rec.school_present_count = sum(1 for att in rec.school_attendance_ids if att.state == "present")

    def action_school_mark_all_present(self):
        """Create ``present`` attendance rows for every enrolled student that
        doesn't already have a row on this session, and mark the session as
        ``completed``."""
        Attendance = self.env["school.attendance"]
        for rec in self:
            if not rec.school_course_id:
                continue
            existing_students = rec.school_attendance_ids.mapped("student_id")
            missing = rec.school_course_id.student_ids - existing_students
            for student in missing:
                Attendance.create(
                    {
                        "student_id": student.id,
                        "session_id": rec.id,
                        "state": "present",
                    }
                )
            rec.school_session_state = "completed"
        return True

    def action_school_cancel_session(self):
        for rec in self:
            if rec.school_course_id:
                rec.school_session_state = "cancelled"
        return True

    def action_open_school_attendance(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendance"),
            "res_model": "school.attendance",
            "view_mode": "list,form",
            "domain": [("session_id", "=", self.id)],
            "context": {
                "default_session_id": self.id,
                "default_course_id": self.school_course_id.id,
            },
        }
