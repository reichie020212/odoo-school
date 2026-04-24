from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_school_shop_item = fields.Boolean(
        help="Marks this product as a school shop item (uniform, textbook, supplies, ...). "
        "Storable (type='product') items are tracked in stock.",
    )
