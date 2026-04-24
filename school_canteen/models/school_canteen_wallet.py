from odoo import _, api, fields, models


class SchoolCanteenWallet(models.Model):
    _name = "school.canteen.wallet"
    _description = "Canteen Student Wallet"
    _order = "student_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_student", "=", True)],
        index=True,
        tracking=True,
    )
    balance = fields.Monetary(default=0.0, readonly=True, tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    state = fields.Selection(
        [("active", "Active"), ("frozen", "Frozen")],
        default="active",
        required=True,
        tracking=True,
    )
    transaction_ids = fields.One2many(
        "school.canteen.transaction",
        "wallet_id",
        string="Transactions",
    )
    topup_total = fields.Monetary(compute="_compute_totals", store=True)
    purchase_total = fields.Monetary(compute="_compute_totals", store=True)
    transaction_count = fields.Integer(compute="_compute_totals", store=True)

    _wallet_student_unique = models.Constraint(
        "UNIQUE(student_id)",
        "A student can only have one canteen wallet.",
    )

    @api.depends("student_id")
    def _compute_name(self):
        for rec in self:
            if rec.student_id and not rec.name:
                rec.name = _("Wallet — %s") % rec.student_id.display_name

    @api.depends("transaction_ids.state", "transaction_ids.type", "transaction_ids.amount")
    def _compute_totals(self):
        for rec in self:
            posted = rec.transaction_ids.filtered(lambda t: t.state == "posted")
            rec.topup_total = sum(t.amount for t in posted if t.type == "topup")
            rec.purchase_total = sum(t.amount for t in posted if t.type == "purchase")
            rec.transaction_count = len(posted)

    def action_freeze(self):
        self.write({"state": "frozen"})

    def action_unfreeze(self):
        self.write({"state": "active"})
