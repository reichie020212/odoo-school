from odoo import api, fields, models


class SchoolShopSaleLine(models.Model):
    _name = "school.shop.sale.line"
    _description = "Shop Sale Line"
    _order = "sale_id, sequence, id"

    sale_id = fields.Many2one(
        "school.shop.sale",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        "product.product",
        required=True,
        domain=[("is_school_shop_item", "=", True)],
    )
    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    quantity = fields.Float(default=1.0, required=True)
    price_unit = fields.Monetary(
        compute="_compute_price_unit",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    subtotal = fields.Monetary(compute="_compute_subtotal", store=True)
    currency_id = fields.Many2one(related="sale_id.currency_id", store=True)

    @api.depends("product_id")
    def _compute_name(self):
        for rec in self:
            if rec.product_id and not rec.name:
                rec.name = rec.product_id.display_name

    @api.depends("product_id")
    def _compute_price_unit(self):
        for rec in self:
            if rec.product_id and not rec.price_unit:
                rec.price_unit = rec.product_id.lst_price

    @api.depends("quantity", "price_unit")
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit
