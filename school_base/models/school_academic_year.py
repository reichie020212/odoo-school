from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolAcademicYear(models.Model):
    _name = "school.academic.year"
    _description = "Academic Year"
    _order = "date_start desc, name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    is_current = fields.Boolean(compute="_compute_is_current", search="_search_is_current")
    term_ids = fields.One2many("school.academic.term", "academic_year_id", string="Terms")
    classroom_ids = fields.One2many("school.classroom", "academic_year_id", string="Classrooms")
    term_count = fields.Integer(compute="_compute_counts")
    classroom_count = fields.Integer(compute="_compute_counts")

    _academic_year_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Academic year code must be unique.",
    )

    @api.depends("state", "date_start", "date_end")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_current = (
                rec.state == "active" and rec.date_start and rec.date_end and rec.date_start <= today <= rec.date_end
            )

    def _search_is_current(self, operator, value):
        today = fields.Date.context_today(self)
        positive = (operator == "=" and value) or (operator == "!=" and not value)
        domain = [
            ("state", "=", "active"),
            ("date_start", "<=", today),
            ("date_end", ">=", today),
        ]
        return domain if positive else ["!", *domain]

    @api.depends("term_ids", "classroom_ids")
    def _compute_counts(self):
        for rec in self:
            rec.term_count = len(rec.term_ids)
            rec.classroom_count = len(rec.classroom_ids)

    @api.constrains("date_start", "date_end")
    def _check_date_range(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(_("End date must be after start date."))

    @api.constrains("state")
    def _check_single_active(self):
        for rec in self:
            if rec.state != "active":
                continue
            other = self.search_count(
                [
                    ("state", "=", "active"),
                    ("id", "!=", rec.id),
                ]
            )
            if other:
                raise ValidationError(_("Only one academic year can be active at a time."))

    def action_activate(self):
        for rec in self:
            rec.state = "active"
        return True

    def action_archive_year(self):
        for rec in self:
            rec.state = "archived"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"
        return True
