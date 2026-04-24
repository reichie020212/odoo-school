from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolAcademicTerm(models.Model):
    _name = "school.academic.term"
    _description = "Academic Term"
    _order = "academic_year_id, sequence, date_start"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    academic_year_id = fields.Many2one(
        "school.academic.year",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    _academic_term_code_year_unique = models.Constraint(
        "UNIQUE(academic_year_id, code)",
        "Term code must be unique within an academic year.",
    )

    @api.constrains("date_start", "date_end")
    def _check_date_range(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(_("Term end date must be after start date."))

    @api.constrains("date_start", "date_end", "academic_year_id")
    def _check_within_year(self):
        for rec in self:
            year = rec.academic_year_id
            if not (rec.date_start and rec.date_end and year.date_start and year.date_end):
                continue
            if rec.date_start < year.date_start or rec.date_end > year.date_end:
                raise ValidationError(
                    _("Term %(term)s dates must fall within academic year %(year)s.")
                    % {"term": rec.name, "year": year.name}
                )

    @api.constrains("date_start", "date_end", "academic_year_id")
    def _check_no_overlap(self):
        for rec in self:
            if not (rec.date_start and rec.date_end and rec.academic_year_id):
                continue
            overlap = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("academic_year_id", "=", rec.academic_year_id.id),
                    ("date_start", "<=", rec.date_end),
                    ("date_end", ">=", rec.date_start),
                ]
            )
            if overlap:
                raise ValidationError(
                    _("Term %(term)s overlaps with another term in the same academic year.") % {"term": rec.name}
                )
