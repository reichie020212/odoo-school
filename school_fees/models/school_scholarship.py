from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolScholarship(models.Model):
    _name = "school.scholarship"
    _description = "Scholarship / Discount"
    _order = "enrollment_id, name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    enrollment_id = fields.Many2one(
        "school.fee.enrollment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    student_id = fields.Many2one(
        related="enrollment_id.student_id",
        store=True,
        index=True,
    )
    discount_type = fields.Selection(
        [("amount", "Fixed Amount"), ("percentage", "Percentage")],
        required=True,
        default="percentage",
        tracking=True,
    )
    discount_amount = fields.Monetary(string="Amount")
    discount_percentage = fields.Float(string="Percentage (0-100)")
    computed_amount = fields.Monetary(compute="_compute_computed_amount", store=True)
    reason = fields.Text()
    state = fields.Selection(
        [("draft", "Draft"), ("applied", "Applied"), ("revoked", "Revoked")],
        default="draft",
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        related="enrollment_id.currency_id",
        store=True,
    )

    @api.depends(
        "discount_type",
        "discount_amount",
        "discount_percentage",
        "enrollment_id.structure_id.total_amount",
    )
    def _compute_computed_amount(self):
        for rec in self:
            if rec.discount_type == "amount":
                rec.computed_amount = rec.discount_amount
            elif rec.discount_type == "percentage":
                base = rec.enrollment_id.structure_id.total_amount or 0.0
                rec.computed_amount = base * (rec.discount_percentage or 0.0) / 100.0
            else:
                rec.computed_amount = 0.0

    @api.constrains("discount_type", "discount_amount", "discount_percentage")
    def _check_discount_fields(self):
        for rec in self:
            if rec.discount_type == "amount":
                if rec.discount_amount <= 0:
                    raise ValidationError(_("Fixed-amount scholarships must have an amount greater than zero."))
                if rec.discount_percentage:
                    raise ValidationError(_("A fixed-amount scholarship must leave the percentage field blank."))
            elif rec.discount_type == "percentage":
                if not (0.0 < rec.discount_percentage <= 100.0):
                    raise ValidationError(_("Percentage scholarships must be between 0 and 100 (exclusive of 0)."))
                if rec.discount_amount:
                    raise ValidationError(_("A percentage scholarship must leave the amount field blank."))

    def action_apply(self):
        for rec in self:
            rec.state = "applied"
        return True

    def action_revoke(self):
        for rec in self:
            if rec.enrollment_id.state == "invoiced":
                raise ValidationError(
                    _(
                        "Revoke this scholarship only after cancelling the linked invoice on "
                        "enrollment %s, then regenerate the invoice."
                    )
                    % rec.enrollment_id.display_name
                )
            rec.state = "revoked"
        return True

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
