from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_BLOOD_TYPES = [
    ("a_pos", "A+"),
    ("a_neg", "A-"),
    ("b_pos", "B+"),
    ("b_neg", "B-"),
    ("ab_pos", "AB+"),
    ("ab_neg", "AB-"),
    ("o_pos", "O+"),
    ("o_neg", "O-"),
    ("unknown", "Unknown"),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_student = fields.Boolean(index=True)
    is_guardian = fields.Boolean(index=True)

    student_admission_number = fields.Char(string="Admission Number", copy=False, index=True)
    student_date_of_birth = fields.Date(string="Date of Birth")
    student_gender = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        string="Gender",
    )
    student_admission_date = fields.Date(
        string="Admission Date",
        default=fields.Date.context_today,
    )
    student_status = fields.Selection(
        [
            ("enrolled", "Enrolled"),
            ("on_leave", "On Leave"),
            ("graduated", "Graduated"),
            ("withdrawn", "Withdrawn"),
        ],
        string="Student Status",
        default="enrolled",
    )
    student_classroom_id = fields.Many2one(
        "school.classroom",
        string="Classroom",
        index=True,
    )
    student_academic_year_id = fields.Many2one(
        "school.academic.year",
        string="Academic Year",
        related="student_classroom_id.academic_year_id",
        store=True,
    )
    student_guardian_ids = fields.Many2many(
        "res.partner",
        relation="school_student_guardian_rel",
        column1="student_id",
        column2="guardian_id",
        domain=[("is_guardian", "=", True)],
        string="Guardians",
    )
    student_ward_ids = fields.Many2many(
        "res.partner",
        relation="school_student_guardian_rel",
        column1="guardian_id",
        column2="student_id",
        domain=[("is_student", "=", True)],
        string="Wards",
    )
    student_medical_notes = fields.Text(string="Medical Notes")
    student_blood_type = fields.Selection(_BLOOD_TYPES, string="Blood Type")
    student_emergency_contact_name = fields.Char(string="Emergency Contact Name")
    student_emergency_contact_phone = fields.Char(string="Emergency Contact Phone")

    _student_admission_number_unique = models.Constraint(
        "UNIQUE(student_admission_number)",
        "Admission number must be unique.",
    )

    @api.constrains("student_date_of_birth")
    def _check_dob_past(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.student_date_of_birth and rec.student_date_of_birth > today:
                raise ValidationError(_("Date of birth must be in the past."))

    @api.constrains("student_guardian_ids")
    def _check_not_self_guardian(self):
        for rec in self:
            if rec in rec.student_guardian_ids:
                raise ValidationError(_("A student cannot be their own guardian."))

    @api.constrains("student_classroom_id", "is_student")
    def _check_classroom_capacity(self):
        # Odoo's @api.constrains on school.classroom.student_ids does not fire when
        # the change comes from the inverse side (this partner's student_classroom_id),
        # so the capacity check has to live here too.
        for rec in self:
            if not (rec.is_student and rec.student_classroom_id):
                continue
            room = rec.student_classroom_id
            if room.capacity and len(room.student_ids) > room.capacity:
                raise ValidationError(
                    _("Classroom %(name)s exceeds capacity (%(count)d students, capacity %(capacity)d).")
                    % {
                        "name": room.name,
                        "count": len(room.student_ids),
                        "capacity": room.capacity,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("is_student") and not vals.get("student_admission_number"):
                vals["student_admission_number"] = (
                    self.env["ir.sequence"].next_by_code("school.student.admission") or False
                )
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("is_student"):
            seq = self.env["ir.sequence"]
            for rec in self:
                if not rec.student_admission_number and not vals.get("student_admission_number"):
                    rec.student_admission_number = seq.next_by_code("school.student.admission") or False
        return super().write(vals)
