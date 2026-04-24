from odoo import http
from odoo.http import request


class SchoolPortalController(http.Controller):
    @http.route("/my/school", type="http", auth="user", website=True)
    def my_school(self, **kwargs):
        env = request.env
        user_partner = env.user.partner_id

        # Resolve which students this user can see data for:
        # - Student user: just themselves.
        # - Guardian: their wards.
        students = env["res.partner"]
        if user_partner.is_student:
            students |= user_partner
        if user_partner.is_guardian:
            students |= user_partner.student_ward_ids

        # Read report cards, exam results, and fee enrollments for those students.
        ReportCard = env["school.report.card"].sudo()
        ExamResult = env["school.exam.result"].sudo()
        FeeEnrollment = env["school.fee.enrollment"].sudo()

        report_cards = ReportCard.search([("student_id", "in", students.ids)], order="issue_date desc", limit=10)
        recent_results = ExamResult.search(
            [("student_id", "in", students.ids)],
            order="create_date desc",
            limit=15,
        )
        fee_enrollments = FeeEnrollment.search([("student_id", "in", students.ids)], order="create_date desc", limit=10)
        outstanding_total = sum(fee_enrollments.mapped("amount_due"))
        currency = fee_enrollments[:1].currency_id or env.company.currency_id

        values = {
            "students": students,
            "report_cards": report_cards,
            "recent_results": recent_results,
            "fee_enrollments": fee_enrollments,
            "outstanding_total": outstanding_total,
            "currency": currency,
            "page_name": "school",
        }
        return request.render("school_portal.portal_my_school", values)
