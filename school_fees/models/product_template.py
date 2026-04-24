from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_school_fee = fields.Boolean(
        help="Marks this product as a school fee item (tuition, lab fee, activity fee, etc.). "
        "Flagged products are selectable on school.fee.structure lines.",
    )
