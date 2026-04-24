from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_canteen_item = fields.Boolean(
        help="Marks this product as a canteen menu item. Flagged items are "
        "selectable on school.canteen.menu rosters and purchase transactions.",
    )
    canteen_dietary_tag_ids = fields.Many2many(
        "school.canteen.dietary.tag",
        "product_template_canteen_dietary_tag_rel",
        "product_tmpl_id",
        "tag_id",
        string="Dietary Tags",
        help="What this product contains. Matched against student allergy tags.",
    )
