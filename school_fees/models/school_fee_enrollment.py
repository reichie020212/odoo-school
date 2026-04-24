from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SchoolFeeEnrollment(models.Model):
    _name = "school.fee.enrollment"
    _description = "Fee Enrollment"
    _order = "term_id desc, student_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_student", "=", True)],
        index=True,
        tracking=True,
    )
    structure_id = fields.Many2one(
        "school.fee.structure",
        required=True,
        index=True,
        tracking=True,
    )
    classroom_id = fields.Many2one(
        related="student_id.student_classroom_id",
        store=True,
    )
    term_id = fields.Many2one(related="structure_id.term_id", store=True, index=True)
    academic_year_id = fields.Many2one(related="structure_id.academic_year_id", store=True)
    scholarship_ids = fields.One2many(
        "school.scholarship",
        "enrollment_id",
        string="Scholarships",
    )
    scholarship_total = fields.Monetary(compute="_compute_amounts", store=True)
    structure_total = fields.Monetary(
        related="structure_id.total_amount",
        store=True,
    )
    amount_total = fields.Monetary(compute="_compute_amounts", store=True)
    amount_paid = fields.Monetary(compute="_compute_amounts", store=True)
    amount_due = fields.Monetary(compute="_compute_amounts", store=True)
    invoice_id = fields.Many2one("account.move", copy=False, readonly=True, tracking=True)
    payment_state = fields.Selection(
        related="invoice_id.payment_state",
        store=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("invoiced", "Invoiced"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(related="structure_id.currency_id", store=True)

    _fee_enrollment_student_structure_unique = models.Constraint(
        "UNIQUE(student_id, structure_id)",
        "A student can only be enrolled in a given fee structure once.",
    )

    @api.depends("student_id", "structure_id")
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.student_id:
                parts.append(rec.student_id.display_name)
            if rec.structure_id:
                parts.append(rec.structure_id.code or rec.structure_id.name or "")
            rec.name = " — ".join(p for p in parts if p) or _("New Fee Enrollment")

    @api.depends(
        "scholarship_ids.state",
        "scholarship_ids.computed_amount",
        "structure_id.total_amount",
        "invoice_id.amount_total",
        "invoice_id.amount_residual",
        "invoice_id.state",
    )
    def _compute_amounts(self):
        for rec in self:
            applied = rec.scholarship_ids.filtered(lambda s: s.state == "applied")
            rec.scholarship_total = sum(applied.mapped("computed_amount"))
            rec.amount_total = max(rec.structure_total - rec.scholarship_total, 0.0)
            invoice = rec.invoice_id
            if invoice and invoice.state == "posted":
                rec.amount_paid = invoice.amount_total - invoice.amount_residual
                rec.amount_due = invoice.amount_residual
            else:
                rec.amount_paid = 0.0
                rec.amount_due = rec.amount_total

    @api.constrains("student_id", "structure_id")
    def _check_grade_matches(self):
        for rec in self:
            if not (rec.student_id and rec.structure_id):
                continue
            classroom = rec.student_id.student_classroom_id
            if classroom and classroom.grade_level != rec.structure_id.grade_level:
                raise ValidationError(
                    _(
                        "Student %(student)s is in grade %(student_grade)s, but the fee "
                        "structure is for %(structure_grade)s."
                    )
                    % {
                        "student": rec.student_id.display_name,
                        "student_grade": dict(classroom._fields["grade_level"].selection).get(
                            classroom.grade_level, classroom.grade_level
                        ),
                        "structure_grade": dict(rec.structure_id._fields["grade_level"].selection).get(
                            rec.structure_id.grade_level, rec.structure_id.grade_level
                        ),
                    }
                )

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                continue
            rec.state = "confirmed"
        return True

    def _prepare_invoice_line_vals(self):
        self.ensure_one()
        lines = []
        for line in self.structure_id.line_ids:
            lines.append(
                {
                    "product_id": line.product_id.id,
                    "name": line.name,
                    "quantity": line.quantity,
                    "price_unit": line.price_unit,
                }
            )
        if lines:
            for scholarship in self.scholarship_ids.filtered(lambda s: s.state == "applied"):
                lines.append(
                    {
                        "name": _("Scholarship: %s") % scholarship.name,
                        "quantity": 1.0,
                        "price_unit": -scholarship.computed_amount,
                        "product_id": self.structure_id.line_ids[0].product_id.id,
                    }
                )
        return lines

    def action_generate_invoice(self):
        AccountMove = self.env["account.move"]
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("Only draft or confirmed enrollments can be invoiced."))
            if rec.invoice_id:
                raise UserError(
                    _("Enrollment %s already has an invoice; cancel it first to regenerate.") % rec.display_name
                )
            invoice = AccountMove.create(
                {
                    "move_type": "out_invoice",
                    "partner_id": rec.student_id.id,
                    "invoice_date": fields.Date.context_today(rec),
                    "invoice_origin": rec.display_name,
                    "invoice_line_ids": [(0, 0, vals) for vals in rec._prepare_invoice_line_vals()],
                }
            )
            # Add guardians as followers so they receive invoice notifications.
            guardians = rec.student_id.student_guardian_ids
            if guardians:
                invoice.message_subscribe(partner_ids=guardians.ids)
            rec.invoice_id = invoice
            rec.state = "invoiced"
        return True

    def action_open_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No invoice generated yet."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
        }

    def action_cancel(self):
        for rec in self:
            if rec.invoice_id and rec.invoice_id.state == "posted":
                raise UserError(
                    _(
                        "Invoice %s is already posted. Reset it to draft from Accounting "
                        "before cancelling this enrollment."
                    )
                    % rec.invoice_id.name
                )
            if rec.invoice_id and rec.invoice_id.state != "cancel":
                rec.invoice_id.button_cancel()
            rec.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("cancelled", "confirmed"):
                continue
            if rec.invoice_id and rec.invoice_id.state == "posted":
                raise UserError(_("Cannot reset to draft while invoice %s is posted.") % rec.invoice_id.name)
            if rec.invoice_id and rec.invoice_id.state == "cancel":
                rec.invoice_id = False
            rec.state = "draft"
        return True
