from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    school_enrollment_ids = fields.One2many(
        "school.fee.enrollment",
        "invoice_id",
        string="Fee Enrollments",
    )
