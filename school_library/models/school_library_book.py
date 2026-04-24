from odoo import api, fields, models


class SchoolLibraryBook(models.Model):
    _name = "school.library.book"
    _description = "Library Book"
    _order = "title"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    title = fields.Char(required=True, tracking=True)
    isbn = fields.Char(string="ISBN", tracking=True)
    author_ids = fields.Many2many("school.library.author", string="Authors")
    category_id = fields.Many2one("school.library.category", string="Category", index=True)
    publisher = fields.Char()
    publish_date = fields.Date()
    summary = fields.Text()
    active = fields.Boolean(default=True)
    copy_ids = fields.One2many("school.library.book.copy", "book_id", string="Copies")
    copy_count = fields.Integer(compute="_compute_copy_counts", store=True)
    available_count = fields.Integer(compute="_compute_copy_counts", store=True)

    _book_isbn_unique = models.Constraint(
        "UNIQUE(isbn)",
        "ISBN must be unique.",
    )

    @api.depends("copy_ids", "copy_ids.state")
    def _compute_copy_counts(self):
        for rec in self:
            rec.copy_count = len(rec.copy_ids)
            rec.available_count = sum(1 for c in rec.copy_ids if c.state == "available")

    def name_get(self):
        return [(rec.id, rec.title) for rec in self]

    @api.depends("title")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.title or ""
