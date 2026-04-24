from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_DEFAULT_LOAN_PERIOD_DAYS = 14
_DEFAULT_FINE_PER_DAY = 5.0


class SchoolLibraryLoan(models.Model):
    _name = "school.library.loan"
    _description = "Library Loan"
    _order = "borrow_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    book_copy_id = fields.Many2one(
        "school.library.book.copy",
        required=True,
        index=True,
        tracking=True,
    )
    book_id = fields.Many2one(
        "school.library.book",
        related="book_copy_id.book_id",
        store=True,
        index=True,
    )
    borrower_id = fields.Many2one(
        "res.partner",
        required=True,
        index=True,
        tracking=True,
    )
    borrow_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    due_date = fields.Date(
        compute="_compute_due_date",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    return_date = fields.Date(tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("borrowed", "Borrowed"),
            ("returned", "Returned"),
            ("returned_late", "Returned (Late)"),
            ("lost", "Lost"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    is_overdue = fields.Boolean(compute="_compute_overdue", store=True)
    overdue_days = fields.Integer(compute="_compute_overdue", store=True)
    fine_amount = fields.Monetary(compute="_compute_overdue", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    @api.depends("book_copy_id", "borrower_id", "borrow_date")
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.book_copy_id and rec.book_copy_id.book_id:
                parts.append(rec.book_copy_id.book_id.title)
            if rec.borrower_id:
                parts.append(rec.borrower_id.display_name)
            if rec.borrow_date:
                parts.append(fields.Date.to_string(rec.borrow_date))
            rec.name = " — ".join(parts) if parts else _("New Loan")

    @api.depends("borrow_date")
    def _compute_due_date(self):
        period = self._get_loan_period_days()
        for rec in self:
            if rec.borrow_date and not rec.due_date:
                rec.due_date = rec.borrow_date + timedelta(days=period)

    @api.depends("state", "due_date", "return_date")
    def _compute_overdue(self):
        rate = self._get_fine_per_day()
        today = fields.Date.context_today(self)
        for rec in self:
            due = rec.due_date
            if rec.state == "borrowed":
                if due and today > due:
                    rec.is_overdue = True
                    rec.overdue_days = (today - due).days
                else:
                    rec.is_overdue = False
                    rec.overdue_days = 0
            elif rec.state == "returned_late":
                rec.is_overdue = True
                rec.overdue_days = (rec.return_date - due).days if (rec.return_date and due) else 0
            else:
                rec.is_overdue = False
                rec.overdue_days = 0
            rec.fine_amount = max(0, rec.overdue_days) * rate

    @api.model
    def _get_loan_period_days(self):
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("school_library.loan_period_days", str(_DEFAULT_LOAN_PERIOD_DAYS))
        )
        try:
            return int(value)
        except (TypeError, ValueError):
            return _DEFAULT_LOAN_PERIOD_DAYS

    @api.model
    def _get_fine_per_day(self):
        value = (
            self.env["ir.config_parameter"].sudo().get_param("school_library.fine_per_day", str(_DEFAULT_FINE_PER_DAY))
        )
        try:
            return float(value)
        except (TypeError, ValueError):
            return _DEFAULT_FINE_PER_DAY

    @api.constrains("borrow_date", "due_date", "return_date")
    def _check_dates(self):
        for rec in self:
            if rec.borrow_date and rec.due_date and rec.due_date <= rec.borrow_date:
                raise ValidationError(_("Due date must be after the borrow date."))
            if rec.return_date and rec.borrow_date and rec.return_date < rec.borrow_date:
                raise ValidationError(_("Return date cannot be before the borrow date."))

    @api.constrains("book_copy_id", "state")
    def _check_copy_available_when_borrowing(self):
        for rec in self:
            if rec.state != "borrowed":
                continue
            # A copy can only be on one active ('borrowed') loan at a time.
            others = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("book_copy_id", "=", rec.book_copy_id.id),
                    ("state", "=", "borrowed"),
                ]
            )
            if others:
                raise ValidationError(_("Copy %s is already on loan.") % rec.book_copy_id.barcode)

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.book_copy_id.state != "available":
                raise UserError(
                    _("Copy %s is not available (current state: %s).")
                    % (rec.book_copy_id.barcode, rec.book_copy_id.state)
                )
            rec.state = "borrowed"
            rec.book_copy_id.state = "borrowed"
        return True

    def action_return(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != "borrowed":
                continue
            rec.return_date = today
            rec.state = "returned_late" if today > rec.due_date else "returned"
            rec.book_copy_id.state = "available"
        return True

    def action_mark_lost(self):
        for rec in self:
            if rec.state not in ("borrowed", "draft"):
                continue
            rec.state = "lost"
            if rec.book_copy_id:
                rec.book_copy_id.state = "lost"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == "draft":
                continue
            # If copy was marked borrowed because of this loan, revert.
            if rec.book_copy_id.state == "borrowed" and rec.book_copy_id.current_loan_id == rec:
                rec.book_copy_id.state = "available"
            rec.state = "draft"
            rec.return_date = False
        return True
