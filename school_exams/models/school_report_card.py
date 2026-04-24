from odoo import _, api, fields, models


class SchoolReportCard(models.Model):
    _name = "school.report.card"
    _description = "Student Report Card"
    _order = "term_id desc, student_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        domain=[("is_student", "=", True)],
        required=True,
        tracking=True,
    )
    term_id = fields.Many2one("school.academic.term", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "school.academic.year",
        related="term_id.academic_year_id",
        store=True,
    )
    line_ids = fields.One2many("school.report.card.line", "report_card_id", string="Courses")
    overall_percentage = fields.Float(compute="_compute_overall", store=True)
    overall_gpa = fields.Float(compute="_compute_overall", store=True)
    overall_letter = fields.Char(compute="_compute_overall", store=True)
    state = fields.Selection(
        [("draft", "Draft"), ("final", "Final"), ("distributed", "Distributed")],
        default="draft",
        required=True,
        tracking=True,
    )
    teacher_remark = fields.Text(string="Overall Remark")
    issue_date = fields.Date(default=fields.Date.context_today, required=True)

    _report_card_student_term_unique = models.Constraint(
        "UNIQUE(student_id, term_id)",
        "A student can only have one report card per term.",
    )

    @api.depends("student_id", "term_id")
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.student_id:
                parts.append(rec.student_id.display_name)
            if rec.term_id:
                parts.append(rec.term_id.academic_year_id.name or "")
                parts.append(rec.term_id.code or "")
            rec.name = " — ".join(p for p in parts if p) or _("New Report Card")

    @api.depends("line_ids.percentage", "line_ids.gpa_value", "line_ids.is_incomplete")
    def _compute_overall(self):
        default_scale = self.env["school.grading.scale"].get_default_scale()
        for rec in self:
            graded_lines = rec.line_ids.filtered(lambda line: not line.is_incomplete)
            if graded_lines:
                rec.overall_percentage = sum(graded_lines.mapped("percentage")) / len(graded_lines)
                rec.overall_gpa = sum(graded_lines.mapped("gpa_value")) / len(graded_lines)
                if default_scale:
                    band = default_scale.band_for_percentage(rec.overall_percentage)
                    rec.overall_letter = band.letter or ""
                else:
                    rec.overall_letter = ""
            else:
                rec.overall_percentage = 0.0
                rec.overall_gpa = 0.0
                rec.overall_letter = ""

    def action_generate_lines(self):
        """Create a line per course the student is enrolled in for this term."""
        Line = self.env["school.report.card.line"]
        Course = self.env["school.course"]
        for rec in self:
            existing_courses = rec.line_ids.mapped("course_id")
            courses = Course.search(
                [
                    ("term_id", "=", rec.term_id.id),
                    ("student_ids", "in", [rec.student_id.id]),
                ]
            )
            for course in courses - existing_courses:
                Line.create({"report_card_id": rec.id, "course_id": course.id})
        return True

    def action_finalize(self):
        for rec in self:
            rec.state = "final"
            rec.line_ids.invalidate_recordset(["percentage", "letter_grade", "gpa_value", "is_incomplete"])
        return True

    def action_distribute(self):
        for rec in self:
            rec.state = "distributed"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"
        return True

    def action_print_report(self):
        return self.env.ref("school_exams.action_report_school_report_card").report_action(self)
