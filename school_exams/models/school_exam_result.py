from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolExamResult(models.Model):
    _name = "school.exam.result"
    _description = "Exam Result"
    _order = "exam_id desc, student_id"
    _rec_name = "student_id"

    exam_id = fields.Many2one(
        "school.exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_student", "=", True)],
        index=True,
        ondelete="restrict",
    )
    course_id = fields.Many2one(
        "school.course",
        related="exam_id.course_id",
        store=True,
        index=True,
    )
    max_score = fields.Float(related="exam_id.max_score", readonly=True)
    score = fields.Float(required=True, default=0.0)
    percentage = fields.Float(compute="_compute_grade", store=True)
    letter_grade = fields.Char(compute="_compute_grade", store=True)
    gpa_value = fields.Float(compute="_compute_grade", store=True)
    remark = fields.Char()

    _exam_result_exam_student_unique = models.Constraint(
        "UNIQUE(exam_id, student_id)",
        "A student can only have one result per exam.",
    )

    @api.depends("score", "exam_id.max_score", "exam_id.effective_scale_id")
    def _compute_grade(self):
        for rec in self:
            max_score = rec.exam_id.max_score or 0.0
            rec.percentage = (rec.score / max_score * 100.0) if max_score else 0.0
            scale = rec.exam_id.effective_scale_id
            if scale:
                band = scale.band_for_percentage(rec.percentage)
                rec.letter_grade = band.letter or ""
                rec.gpa_value = band.gpa_value
            else:
                rec.letter_grade = ""
                rec.gpa_value = 0.0

    @api.constrains("score", "exam_id")
    def _check_score_range(self):
        for rec in self:
            if rec.score < 0:
                raise ValidationError(_("Score cannot be negative."))
            if rec.exam_id.max_score and rec.score > rec.exam_id.max_score:
                raise ValidationError(
                    _("Score %(score)s exceeds maximum %(max)s for exam %(exam)s.")
                    % {
                        "score": rec.score,
                        "max": rec.exam_id.max_score,
                        "exam": rec.exam_id.display_name,
                    }
                )

    @api.constrains("student_id", "exam_id")
    def _check_student_enrolled(self):
        for rec in self:
            course = rec.exam_id.course_id
            if not course:
                continue
            if rec.student_id not in course.student_ids:
                raise ValidationError(
                    _("Student %(student)s is not enrolled in course %(course)s.")
                    % {"student": rec.student_id.display_name, "course": course.display_name}
                )
