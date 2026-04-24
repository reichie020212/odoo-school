from odoo import _, api, fields, models


class SchoolCanteenMenu(models.Model):
    _name = "school.canteen.menu"
    _description = "Canteen Daily Menu"
    _order = "date desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    item_ids = fields.Many2many(
        "product.product",
        "school_canteen_menu_item_rel",
        "menu_id",
        "product_id",
        domain=[("is_canteen_item", "=", True)],
        string="Items",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published"), ("closed", "Closed")],
        default="draft",
        required=True,
    )
    item_count = fields.Integer(compute="_compute_item_count", store=True)

    @api.depends("date")
    def _compute_name(self):
        for rec in self:
            if rec.date and not rec.name:
                rec.name = _("Menu %s") % fields.Date.to_string(rec.date)

    @api.depends("item_ids")
    def _compute_item_count(self):
        for rec in self:
            rec.item_count = len(rec.item_ids)

    def action_publish(self):
        self.write({"state": "published"})

    def action_close(self):
        self.write({"state": "closed"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
