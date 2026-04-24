from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SchoolShopSale(models.Model):
    _name = "school.shop.sale"
    _description = "Shop Sale"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    buyer_id = fields.Many2one(
        "res.partner",
        string="Buyer",
        required=True,
        index=True,
        tracking=True,
        help="Who receives the goods — a student, guardian, or any partner.",
    )
    date = fields.Date(default=fields.Date.context_today, required=True)
    line_ids = fields.One2many("school.shop.sale.line", "sale_id", string="Items")
    total_amount = fields.Monetary(compute="_compute_total", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    picking_id = fields.Many2one(
        "stock.picking",
        string="Delivery",
        copy=False,
        readonly=True,
    )
    picking_state = fields.Selection(related="picking_id.state", store=True)
    note = fields.Char()

    @api.depends("buyer_id", "date")
    def _compute_name(self):
        for rec in self:
            if rec.name:
                continue
            parts = []
            if rec.buyer_id:
                parts.append(rec.buyer_id.display_name)
            if rec.date:
                parts.append(fields.Date.to_string(rec.date))
            rec.name = _("Shop Sale — %s") % " ".join(parts) if parts else _("New Shop Sale")

    @api.depends("line_ids.subtotal")
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("subtotal"))

    def _get_outgoing_picking_type(self):
        """Return a default outgoing picking type from the main warehouse, if any."""
        picking_type = self.env.ref("stock.picking_type_out", raise_if_not_found=False)
        if picking_type:
            return picking_type
        return self.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )

    def _prepare_picking_vals(self, picking_type):
        self.ensure_one()
        location_id = picking_type.default_location_src_id.id
        location_dest_id = (
            self.buyer_id.property_stock_customer.id
            if self.buyer_id.property_stock_customer
            else self.env.ref("stock.stock_location_customers").id
        )
        return {
            "partner_id": self.buyer_id.id,
            "picking_type_id": picking_type.id,
            "location_id": location_id,
            "location_dest_id": location_dest_id,
            "origin": self.name,
            "move_ids": [
                (
                    0,
                    0,
                    {
                        "name": line.name,
                        "product_id": line.product_id.id,
                        "product_uom_qty": line.quantity,
                        "product_uom": line.product_id.uom_id.id,
                        "location_id": location_id,
                        "location_dest_id": location_dest_id,
                    },
                )
                for line in self.line_ids
                if line.product_id.is_storable or line.product_id.type == "product"
            ],
        }

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if not rec.line_ids:
                raise UserError(_("Cannot confirm a sale with no items."))
            picking_type = rec._get_outgoing_picking_type()
            storable_lines = [
                line
                for line in rec.line_ids
                if line.product_id.type == "product" or getattr(line.product_id, "is_storable", False)
            ]
            if picking_type and storable_lines:
                picking = self.env["stock.picking"].create(rec._prepare_picking_vals(picking_type))
                picking.action_confirm()
                picking.action_assign()
                rec.picking_id = picking
            rec.state = "confirmed"
        return True

    def action_cancel(self):
        for rec in self:
            if rec.picking_id and rec.picking_id.state not in ("done", "cancel"):
                rec.picking_id.action_cancel()
            rec.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == "draft":
                continue
            if rec.picking_id and rec.picking_id.state == "done":
                raise UserError(_("Delivery %s is already done; cannot reset to draft.") % rec.picking_id.name)
            if rec.picking_id and rec.picking_id.state != "cancel":
                rec.picking_id.action_cancel()
            rec.picking_id = False
            rec.state = "draft"
        return True

    def action_open_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError(_("No delivery associated with this sale."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": self.picking_id.id,
            "view_mode": "form",
        }
