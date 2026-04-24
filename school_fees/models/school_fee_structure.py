from odoo import _, api, fields, models

GRADE_LEVELS = [
    ("k", "Kindergarten"),
    ("1", "Grade 1"),
    ("2", "Grade 2"),
    ("3", "Grade 3"),
    ("4", "Grade 4"),
    ("5", "Grade 5"),
    ("6", "Grade 6"),
    ("7", "Grade 7"),
    ("8", "Grade 8"),
    ("9", "Grade 9"),
    ("10", "Grade 10"),
    ("11", "Grade 11"),
    ("12", "Grade 12"),
]


class SchoolFeeStructure(models.Model):
    _name = "school.fee.structure"
    _description = "Fee Structure"
    _order = "term_id desc, grade_level"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    code = fields.Char(required=True, tracking=True)
    grade_level = fields.Selection(GRADE_LEVELS, required=True, tracking=True)
    term_id = fields.Many2one("school.academic.term", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "school.academic.year",
        related="term_id.academic_year_id",
        store=True,
    )
    line_ids = fields.One2many("school.fee.structure.line", "structure_id", string="Items")
    total_amount = fields.Monetary(compute="_compute_total_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("closed", "Closed")],
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    _fee_structure_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Fee structure code must be unique.",
    )
    _fee_structure_grade_term_unique = models.Constraint(
        "UNIQUE(grade_level, term_id)",
        "A fee structure already exists for this grade and term.",
    )

    @api.depends("grade_level", "term_id")
    def _compute_name(self):
        grade_lookup = dict(GRADE_LEVELS)
        for rec in self:
            parts = []
            if rec.grade_level:
                parts.append(grade_lookup.get(rec.grade_level, rec.grade_level))
            if rec.term_id:
                parts.append(rec.term_id.code)
            if rec.term_id and rec.term_id.academic_year_id:
                parts.append(rec.term_id.academic_year_id.name)
            rec.name = " — ".join(parts) if parts else _("New Fee Structure")

    @api.depends("line_ids.subtotal")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("subtotal"))

    def action_open(self):
        self.write({"state": "open"})

    def action_close(self):
        self.write({"state": "closed"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
