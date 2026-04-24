from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolGradingScale(models.Model):
    _name = "school.grading.scale"
    _description = "Grading Scale"
    _order = "is_default desc, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    is_default = fields.Boolean(
        help="Exactly one grading scale is the system default and is used when an exam does not specify its own scale.",
    )
    active = fields.Boolean(default=True)
    band_ids = fields.One2many("school.grading.scale.band", "scale_id", string="Bands")

    _grading_scale_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Grading scale code must be unique.",
    )

    @api.constrains("is_default", "active")
    def _check_single_default(self):
        for rec in self:
            if not rec.is_default:
                continue
            other = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("is_default", "=", True),
                    ("active", "=", True),
                ]
            )
            if other:
                raise ValidationError(_("Only one grading scale can be the default at a time."))

    @api.model
    def get_default_scale(self):
        return self.search([("is_default", "=", True)], limit=1)

    def band_for_percentage(self, percentage):
        """Return the matching band for a given percentage.

        The highest-`min_percentage` band whose threshold is ≤ percentage wins.
        Returns the lowest band when the percentage is below every band (so a
        letter_grade is always produced).
        """
        self.ensure_one()
        bands = self.band_ids.sorted(key=lambda b: b.min_percentage, reverse=True)
        if not bands:
            return self.env["school.grading.scale.band"]
        for band in bands:
            if percentage >= band.min_percentage:
                return band
        return bands[-1]
