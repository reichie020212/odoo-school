from odoo import api, fields, models


class SchoolReportCardLine(models.Model):
    _name = "school.report.card.line"
    _description = "Report Card Line"
    _order = "subject_id"

    report_card_id = fields.Many2one(
        "school.report.card",
        required=True,
        ondelete="cascade",
        index=True,
    )
    student_id = fields.Many2one(
        related="report_card_id.student_id",
        store=True,
        index=True,
    )
    course_id = fields.Many2one("school.course", required=True)
    subject_id = fields.Many2one(
        related="course_id.subject_id",
        store=True,
        index=True,
    )
    teacher_id = fields.Many2one(related="course_id.teacher_id", store=True)
    percentage = fields.Float(compute="_compute_grade", store=True)
    letter_grade = fields.Char(compute="_compute_grade", store=True)
    gpa_value = fields.Float(compute="_compute_grade", store=True)
    is_incomplete = fields.Boolean(compute="_compute_grade", store=True)
    teacher_remark = fields.Char()

    _report_card_line_unique = models.Constraint(
        "UNIQUE(report_card_id, course_id)",
        "A report card can only have one line per course.",
    )

    @api.depends(
        "course_id",
        "student_id",
        "report_card_id.term_id",
    )
    def _compute_grade(self):
        ExamResult = self.env["school.exam.result"]
        default_scale = self.env["school.grading.scale"].get_default_scale()
        for rec in self:
            rec.percentage = 0.0
            rec.letter_grade = ""
            rec.gpa_value = 0.0
            rec.is_incomplete = True
            if not (rec.course_id and rec.student_id and rec.report_card_id.term_id):
                continue
            results = ExamResult.search(
                [
                    ("course_id", "=", rec.course_id.id),
                    ("student_id", "=", rec.student_id.id),
                    ("exam_id.state", "in", ("published", "closed")),
                    ("exam_id.weight", ">", 0),
                    ("exam_id.course_id.term_id", "=", rec.report_card_id.term_id.id),
                ]
            )
            if not results:
                continue
            total_weight = sum(results.mapped("exam_id.weight"))
            if not total_weight:
                continue
            weighted = sum(r.percentage * r.exam_id.weight for r in results)
            rec.percentage = weighted / total_weight
            rec.is_incomplete = False
            # Use the first contributing exam's scale; fall back to the global default.
            scale = results[:1].exam_id.effective_scale_id or default_scale
            if scale:
                band = scale.band_for_percentage(rec.percentage)
                rec.letter_grade = band.letter or ""
                rec.gpa_value = band.gpa_value
