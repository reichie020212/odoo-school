from odoo import fields, models


class SchoolLibraryAuthor(models.Model):
    _name = "school.library.author"
    _description = "Library Author"
    _order = "name"

    name = fields.Char(required=True, index=True)
    bio = fields.Text()
    active = fields.Boolean(default=True)
    book_ids = fields.Many2many("school.library.book", string="Books")
    book_count = fields.Integer(compute="_compute_book_count")

    def _compute_book_count(self):
        for rec in self:
            rec.book_count = len(rec.book_ids)
