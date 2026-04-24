from odoo import fields, models


class SchoolExamType(models.Model):
    _name = "school.exam.type"
    _description = "Exam Type"
    _order = "sequence, code"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    default_weight = fields.Float(
        string="Default Weight",
        default=25.0,
        help="Percent contribution to the course grade, seeded onto new exams.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _exam_type_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Exam type code must be unique.",
    )
