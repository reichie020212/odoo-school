from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SchoolCanteenTransaction(models.Model):
    _name = "school.canteen.transaction"
    _description = "Canteen Transaction"
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
    wallet_id = fields.Many2one(
        "school.canteen.wallet",
        required=True,
        index=True,
        ondelete="cascade",
        tracking=True,
    )
    student_id = fields.Many2one(
        related="wallet_id.student_id",
        store=True,
        index=True,
    )
    type = fields.Selection(
        [("topup", "Top-up"), ("purchase", "Purchase")],
        required=True,
        default="topup",
        tracking=True,
    )
    date = fields.Date(default=fields.Date.context_today, required=True)
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    item_ids = fields.Many2many(
        "product.product",
        "canteen_transaction_item_rel",
        "transaction_id",
        "product_id",
        domain=[("is_canteen_item", "=", True)],
        string="Items",
    )
    method = fields.Selection(
        [("cash", "Cash"), ("bank", "Bank Transfer"), ("card", "Card"), ("other", "Other")],
        default="cash",
    )
    description = fields.Char()
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    posted_at = fields.Datetime(readonly=True)
    currency_id = fields.Many2one(related="wallet_id.currency_id", store=True)

    @api.depends("type", "wallet_id", "date")
    def _compute_name(self):
        for rec in self:
            if rec.name:
                continue
            type_label = dict(rec._fields["type"].selection).get(rec.type or "topup", "")
            student = rec.wallet_id.student_id.display_name if rec.wallet_id else ""
            parts = [p for p in (type_label, student, fields.Date.to_string(rec.date) if rec.date else "") if p]
            rec.name = " — ".join(parts) if parts else _("New Transaction")

    @api.depends("type", "item_ids", "item_ids.lst_price")
    def _compute_amount(self):
        for rec in self:
            if rec.type == "purchase":
                rec.amount = sum(item.lst_price for item in rec.item_ids)
            # top-up amount stays user-entered

    @api.constrains("amount")
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Transaction amount must be greater than zero."))

    @api.constrains("type", "item_ids", "wallet_id", "state")
    def _check_purchase_allergy(self):
        for rec in self:
            if rec.type != "purchase" or not rec.item_ids:
                continue
            if rec.state == "cancelled":
                continue
            student = rec.wallet_id.student_id
            student_allergies = set(student.canteen_allergy_tag_ids.ids)
            if not student_allergies:
                continue
            conflicting_items = []
            for item in rec.item_ids:
                item_tags = set(item.canteen_dietary_tag_ids.ids)
                if item_tags & student_allergies:
                    conflicting_items.append(item.display_name)
            if conflicting_items:
                raise ValidationError(
                    _("%(student)s is allergic to something in: %(items)s.")
                    % {"student": student.display_name, "items": ", ".join(conflicting_items)}
                )

    def action_post(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Only draft transactions can be posted."))
            if rec.wallet_id.state != "active":
                raise UserError(_("Wallet %s is not active.") % rec.wallet_id.display_name)
            if rec.type == "purchase" and rec.wallet_id.balance < rec.amount:
                raise UserError(
                    _("Insufficient balance: wallet has %(balance)s, purchase requires %(amount)s.")
                    % {"balance": rec.wallet_id.balance, "amount": rec.amount}
                )
            if rec.type == "topup":
                rec.wallet_id.balance += rec.amount
            else:
                rec.wallet_id.balance -= rec.amount
            rec.state = "posted"
            rec.posted_at = fields.Datetime.now()
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == "cancelled":
                continue
            if rec.state == "posted":
                # reverse the balance change
                if rec.type == "topup":
                    rec.wallet_id.balance -= rec.amount
                else:
                    rec.wallet_id.balance += rec.amount
            rec.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == "posted":
                raise UserError(_("Cancel the transaction first to reverse the balance."))
            rec.state = "draft"
        return True
