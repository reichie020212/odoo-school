from odoo import fields, models


class SchoolCanteenDietaryTag(models.Model):
    _name = "school.canteen.dietary.tag"
    _description = "Canteen Dietary Tag"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Short machine code e.g. 'nuts', 'gluten'.")
    description = fields.Char()
    color = fields.Integer(default=0)
    active = fields.Boolean(default=True)

    _dietary_tag_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Dietary tag code must be unique.",
    )
