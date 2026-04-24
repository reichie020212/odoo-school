from datetime import date as date_cls
from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .school_course_schedule_rule import WEEKDAY_TO_INDEX


class SchoolCourse(models.Model):
    _name = "school.course"
    _description = "School Course"
    _order = "term_id desc, classroom_id, subject_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    subject_id = fields.Many2one("school.subject", required=True, tracking=True)
    term_id = fields.Many2one("school.academic.term", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "school.academic.year",
        related="term_id.academic_year_id",
        store=True,
        string="Academic Year",
    )
    teacher_id = fields.Many2one(
        "hr.employee",
        string="Teacher",
        domain=[("is_teacher", "=", True)],
        required=True,
        tracking=True,
    )
    classroom_id = fields.Many2one("school.classroom", required=True, tracking=True)
    student_ids = fields.Many2many(
        "res.partner",
        "school_course_student_rel",
        "course_id",
        "student_id",
        string="Enrolled Students",
        domain=[("is_student", "=", True)],
    )
    student_count = fields.Integer(compute="_compute_student_count", store=True)
    schedule_rule_ids = fields.One2many(
        "school.course.schedule.rule",
        "course_id",
        string="Weekly Schedule",
    )
    session_ids = fields.One2many(
        "calendar.event",
        "school_course_id",
        string="Sessions",
    )
    session_count = fields.Integer(compute="_compute_session_count", store=True)
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("closed", "Closed")],
        default="draft",
        required=True,
        tracking=True,
    )
    color = fields.Integer()

    _course_subject_classroom_term_unique = models.Constraint(
        "UNIQUE(subject_id, classroom_id, term_id)",
        "A course for the same subject, classroom, and term already exists.",
    )

    @api.depends("subject_id", "classroom_id", "term_id")
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.subject_id:
                parts.append(rec.subject_id.name)
            if rec.classroom_id:
                parts.append(rec.classroom_id.code)
            if rec.term_id:
                parts.append(rec.term_id.code)
            rec.name = " — ".join(parts) if parts else _("New Course")

    @api.depends("student_ids")
    def _compute_student_count(self):
        for rec in self:
            rec.student_count = len(rec.student_ids)

    @api.depends("session_ids")
    def _compute_session_count(self):
        for rec in self:
            rec.session_count = len(rec.session_ids)

    @api.model_create_multi
    def create(self, vals_list):
        courses = super().create(vals_list)
        # Seed enrolled students from classroom roster when enrollment wasn't
        # specified explicitly. Using a post-create fill lets us access the
        # related classroom's students cleanly regardless of vals ordering.
        for course, vals in zip(courses, vals_list, strict=True):
            if "student_ids" in vals:
                continue
            if course.classroom_id and course.classroom_id.student_ids:
                course.student_ids = [(6, 0, course.classroom_id.student_ids.ids)]
        return courses

    def action_reset_enrollment(self):
        """Reseed enrolled students from the current classroom roster."""
        for rec in self:
            rec.student_ids = [(6, 0, rec.classroom_id.student_ids.ids)]
        return True

    def action_open(self):
        for rec in self:
            rec.state = "open"
        return True

    def action_close(self):
        for rec in self:
            rec.state = "closed"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"
        return True

    def action_materialize_sessions(self):
        """Create ``calendar.event`` sessions from this course's weekly schedule
        across the term date range. Idempotent — sessions already created (same
        course + date + start time) are skipped."""
        self.ensure_one()
        if not self.schedule_rule_ids:
            raise UserError(_("Add at least one weekly schedule rule before materialising sessions."))
        if not (self.term_id.date_start and self.term_id.date_end):
            raise UserError(_("Term %s must have start and end dates.") % self.term_id.name)

        CalendarEvent = self.env["calendar.event"]
        classroom_name = self.classroom_id.name
        attendee_partners = self.student_ids | self.teacher_id.work_contact_id

        # Cache existing (date, time_start) tuples to skip duplicates.
        existing = {
            (ev.start.date(), round(ev.start.hour + ev.start.minute / 60.0, 4)) for ev in self.session_ids if ev.start
        }

        created = self.env["calendar.event"]
        day = self.term_id.date_start
        end = self.term_id.date_end
        while day <= end:
            for rule in self.schedule_rule_ids:
                if WEEKDAY_TO_INDEX[rule.weekday] != day.weekday():
                    continue
                start_time_key = round(rule.time_start, 4)
                if (day, start_time_key) in existing:
                    continue
                hours = int(rule.time_start)
                minutes = int(round((rule.time_start - hours) * 60))
                start_dt = datetime.combine(day, time(hour=hours, minute=minutes))
                stop_dt = start_dt + timedelta(hours=rule.duration)
                event = CalendarEvent.create(
                    {
                        "name": f"{self.subject_id.name} — {self.classroom_id.code}",
                        "start": start_dt,
                        "stop": stop_dt,
                        "duration": rule.duration,
                        "location": rule.location or classroom_name,
                        "school_course_id": self.id,
                        "school_session_state": "scheduled",
                        "partner_ids": [(6, 0, attendee_partners.ids)],
                        "user_id": self.env.user.id,
                    }
                )
                created |= event
                existing.add((day, start_time_key))
            day += timedelta(days=1)

        if not created:
            raise UserError(_("No new sessions created — all dates are already materialised."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Sessions"),
            "res_model": "calendar.event",
            "view_mode": "list,calendar,form",
            "domain": [("school_course_id", "=", self.id)],
            "context": {"default_school_course_id": self.id},
        }

    def action_open_sessions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sessions"),
            "res_model": "calendar.event",
            "view_mode": "list,calendar,form",
            "domain": [("school_course_id", "=", self.id)],
            "context": {"default_school_course_id": self.id},
        }

    def action_open_attendance(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendance"),
            "res_model": "school.attendance",
            "view_mode": "list,form",
            "domain": [("course_id", "=", self.id)],
            "context": {"default_course_id": self.id},
        }

    # Helper used by tests to avoid relying on Odoo's registry for date math.
    @staticmethod
    def _materialize_date_iter(start: date_cls, end: date_cls):
        day = start
        while day <= end:
            yield day
            day += timedelta(days=1)
