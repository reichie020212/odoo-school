from odoo import api, fields, models


class SchoolLibraryBookCopy(models.Model):
    _name = "school.library.book.copy"
    _description = "Library Book Copy"
    _order = "book_id, barcode"
    _rec_name = "barcode"

    book_id = fields.Many2one(
        "school.library.book",
        required=True,
        ondelete="cascade",
        index=True,
    )
    barcode = fields.Char(required=True, index=True, copy=False)
    state = fields.Selection(
        [
            ("available", "Available"),
            ("borrowed", "Borrowed"),
            ("lost", "Lost"),
            ("damaged", "Damaged"),
        ],
        default="available",
        required=True,
    )
    notes = fields.Char()
    active = fields.Boolean(default=True)
    loan_ids = fields.One2many("school.library.loan", "book_copy_id", string="Loans")
    current_loan_id = fields.Many2one(
        "school.library.loan",
        compute="_compute_current_loan",
        store=True,
    )

    _book_copy_barcode_unique = models.Constraint(
        "UNIQUE(barcode)",
        "Barcode must be unique.",
    )

    @api.depends("loan_ids", "loan_ids.state")
    def _compute_current_loan(self):
        for rec in self:
            active_loan = rec.loan_ids.filtered(lambda loan: loan.state == "borrowed")
            rec.current_loan_id = active_loan[:1]
