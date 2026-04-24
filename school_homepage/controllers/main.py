from odoo import http
from odoo.http import request


class SchoolHomepage(http.Controller):
    """Custom root ``/`` controller for the School Management System."""

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def school_home(self, **kwargs):
        env = request.env
        Student = env["res.partner"].sudo()
        Employee = env["hr.employee"].sudo()
        Classroom = env["school.classroom"].sudo()
        Course = env["school.course"].sudo()
        Book = env["school.library.book"].sudo()

        values = {
            "school_name": env.company.name,
            "school_logo_url": f"/web/image/res.company/{env.company.id}/logo",
            "stat_students": Student.search_count([("is_student", "=", True)]),
            "stat_teachers": Employee.search_count([("is_teacher", "=", True)]),
            "stat_classrooms": Classroom.search_count([]),
            "stat_courses": Course.search_count([]),
            "stat_books": Book.search_count([]),
        }
        return request.render("school_homepage.homepage", values)
