from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_teacher = fields.Boolean(index=True)
    teacher_employee_number = fields.Char(string="School Employee Number", copy=False, index=True)
    teacher_qualifications = fields.Text(string="Qualifications")
    teacher_homeroom_ids = fields.One2many(
        "school.classroom",
        "homeroom_teacher_id",
        string="Homeroom Classrooms",
    )
    teacher_hire_date = fields.Date(string="School Hire Date")

    _teacher_employee_number_unique = models.Constraint(
        "UNIQUE(teacher_employee_number)",
        "School employee number must be unique.",
    )
