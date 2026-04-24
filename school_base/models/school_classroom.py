from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolClassroom(models.Model):
    _name = "school.classroom"
    _description = "Classroom"
    _order = "academic_year_id desc, grade_level, section, code"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Short code, unique per academic year (e.g. 10A).")
    grade_level = fields.Selection(
        [
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
        ],
        required=True,
    )
    section = fields.Char(help="Section label, e.g. A / B / C.")
    capacity = fields.Integer(default=30)
    academic_year_id = fields.Many2one(
        "school.academic.year",
        required=True,
        ondelete="restrict",
        index=True,
    )
    homeroom_teacher_id = fields.Many2one(
        "hr.employee",
        string="Homeroom Teacher",
        domain=[("is_teacher", "=", True)],
    )
    student_ids = fields.One2many(
        "res.partner",
        "student_classroom_id",
        domain=[("is_student", "=", True)],
        string="Students",
    )
    student_count = fields.Integer(compute="_compute_student_count", store=True)

    _classroom_code_year_unique = models.Constraint(
        "UNIQUE(academic_year_id, code)",
        "Classroom code must be unique within an academic year.",
    )

    @api.depends("student_ids")
    def _compute_student_count(self):
        for rec in self:
            rec.student_count = len(rec.student_ids)

    @api.constrains("capacity", "student_ids")
    def _check_capacity(self):
        for rec in self:
            if rec.capacity and len(rec.student_ids) > rec.capacity:
                raise ValidationError(
                    _("Classroom %(name)s exceeds capacity (%(count)d students, capacity %(capacity)d).")
                    % {
                        "name": rec.name,
                        "count": len(rec.student_ids),
                        "capacity": rec.capacity,
                    }
                )

    @api.constrains("homeroom_teacher_id")
    def _check_homeroom_is_teacher(self):
        for rec in self:
            if rec.homeroom_teacher_id and not rec.homeroom_teacher_id.is_teacher:
                raise ValidationError(_("Homeroom teacher must be flagged as a teacher."))
