from odoo import fields, models


class SchoolSubject(models.Model):
    _name = "school.subject"
    _description = "School Subject"
    _order = "code"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    description = fields.Text()
    default_weekly_hours = fields.Float(
        string="Default Weekly Hours",
        default=3.0,
        help="Default weekly hours for courses created from this subject.",
    )
    active = fields.Boolean(default=True)
    course_ids = fields.One2many("school.course", "subject_id", string="Courses")
    course_count = fields.Integer(compute="_compute_course_count")

    _subject_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Subject code must be unique.",
    )

    def _compute_course_count(self):
        groups = self.env["school.course"]._read_group(
            [("subject_id", "in", self.ids)],
            groupby=["subject_id"],
            aggregates=["__count"],
        )
        counts = {subject.id: count for subject, count in groups}
        for rec in self:
            rec.course_count = counts.get(rec.id, 0)
