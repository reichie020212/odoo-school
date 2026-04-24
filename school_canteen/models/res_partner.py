from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    canteen_allergy_tag_ids = fields.Many2many(
        "school.canteen.dietary.tag",
        "res_partner_canteen_allergy_tag_rel",
        "partner_id",
        "tag_id",
        string="Canteen Allergies",
        help="Tags a student is allergic to. Purchases containing these are blocked.",
    )
