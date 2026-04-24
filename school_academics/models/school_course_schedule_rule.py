from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

WEEKDAYS = [
    ("mon", "Monday"),
    ("tue", "Tuesday"),
    ("wed", "Wednesday"),
    ("thu", "Thursday"),
    ("fri", "Friday"),
    ("sat", "Saturday"),
    ("sun", "Sunday"),
]

WEEKDAY_TO_INDEX = {code: idx for idx, (code, _label) in enumerate(WEEKDAYS)}


class SchoolCourseScheduleRule(models.Model):
    _name = "school.course.schedule.rule"
    _description = "Course Weekly Schedule Rule"
    _order = "course_id, weekday, time_start"

    course_id = fields.Many2one(
        "school.course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    weekday = fields.Selection(WEEKDAYS, required=True)
    time_start = fields.Float(
        string="Start Time",
        required=True,
        help="Start time in 24h format; e.g. 10.5 = 10:30.",
    )
    duration = fields.Float(
        required=True,
        default=1.0,
        help="Session duration in hours.",
    )
    location = fields.Char(
        help="Optional location override; defaults to the course's classroom when blank.",
    )

    @api.constrains("time_start")
    def _check_time_start(self):
        for rec in self:
            if not (0 <= rec.time_start < 24):
                raise ValidationError(_("Start time must be between 00:00 and 24:00."))

    @api.constrains("duration")
    def _check_duration(self):
        for rec in self:
            if not (0 < rec.duration <= 8):
                raise ValidationError(_("Duration must be greater than 0 and at most 8 hours."))
