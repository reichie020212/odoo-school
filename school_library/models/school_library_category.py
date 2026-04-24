from odoo import fields, models


class SchoolLibraryCategory(models.Model):
    _name = "school.library.category"
    _description = "Library Category"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    description = fields.Char()
    active = fields.Boolean(default=True)
    book_ids = fields.One2many("school.library.book", "category_id", string="Books")
    book_count = fields.Integer(compute="_compute_book_count")

    def _compute_book_count(self):
        for rec in self:
            rec.book_count = len(rec.book_ids)
