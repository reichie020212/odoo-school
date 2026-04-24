from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolGradingScaleBand(models.Model):
    _name = "school.grading.scale.band"
    _description = "Grading Scale Band"
    _order = "scale_id, sequence, min_percentage desc"

    scale_id = fields.Many2one(
        "school.grading.scale",
        required=True,
        ondelete="cascade",
        index=True,
    )
    letter = fields.Char(required=True)
    min_percentage = fields.Float(
        string="Minimum %",
        required=True,
        help="Inclusive lower bound; the highest-matching band wins.",
    )
    gpa_value = fields.Float(string="GPA", default=0.0)
    sequence = fields.Integer(default=10)

    @api.constrains("min_percentage")
    def _check_min_percentage_range(self):
        for rec in self:
            if not (0.0 <= rec.min_percentage <= 100.0):
                raise ValidationError(_("Minimum percentage must be between 0 and 100."))
