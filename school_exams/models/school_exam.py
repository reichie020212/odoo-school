from odoo import _, api, fields, models


class SchoolExam(models.Model):
    _name = "school.exam"
    _description = "Exam"
    _order = "date desc, course_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    course_id = fields.Many2one("school.course", required=True, tracking=True)
    exam_type_id = fields.Many2one("school.exam.type", required=True, tracking=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    max_score = fields.Float(default=100.0, required=True)
    weight = fields.Float(
        compute="_compute_weight",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        help="Percent contribution of this exam to the course grade.",
    )
    grading_scale_id = fields.Many2one(
        "school.grading.scale",
        string="Grading Scale Override",
        help="Leave blank to use the default scale.",
    )
    effective_scale_id = fields.Many2one(
        "school.grading.scale",
        compute="_compute_effective_scale",
        string="Effective Scale",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published"), ("closed", "Closed")],
        default="draft",
        required=True,
        tracking=True,
    )
    result_ids = fields.One2many("school.exam.result", "exam_id", string="Results")
    result_count = fields.Integer(compute="_compute_result_stats", store=True)
    average_percentage = fields.Float(compute="_compute_result_stats", store=True)

    @api.depends("course_id", "exam_type_id", "date")
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.exam_type_id:
                parts.append(rec.exam_type_id.name)
            if rec.course_id:
                parts.append(rec.course_id.name)
            if rec.date:
                parts.append(fields.Date.to_string(rec.date))
            rec.name = " — ".join(parts) if parts else _("New Exam")

    @api.depends("exam_type_id")
    def _compute_weight(self):
        for rec in self:
            if rec.exam_type_id and not rec.weight:
                rec.weight = rec.exam_type_id.default_weight

    @api.depends("grading_scale_id")
    def _compute_effective_scale(self):
        default = self.env["school.grading.scale"].get_default_scale()
        for rec in self:
            rec.effective_scale_id = rec.grading_scale_id or default

    @api.depends("result_ids", "result_ids.percentage")
    def _compute_result_stats(self):
        for rec in self:
            rec.result_count = len(rec.result_ids)
            if rec.result_ids:
                rec.average_percentage = sum(rec.result_ids.mapped("percentage")) / len(rec.result_ids)
            else:
                rec.average_percentage = 0.0

    def action_publish(self):
        for rec in self:
            rec.state = "published"
        return True

    def action_close(self):
        for rec in self:
            rec.state = "closed"
        return True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"
        return True

    def action_generate_result_placeholders(self):
        """Create a blank score row for every enrolled student missing one."""
        Result = self.env["school.exam.result"]
        for rec in self:
            existing_students = rec.result_ids.mapped("student_id")
            for student in rec.course_id.student_ids - existing_students:
                Result.create(
                    {
                        "exam_id": rec.id,
                        "student_id": student.id,
                        "score": 0.0,
                    }
                )
        return True
