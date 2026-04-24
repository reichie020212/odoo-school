{
    "name": "School Base",
    "version": "19.0.1.0.0",
    "summary": "Foundation module for the School Management System",
    "description": """
School Base
===========
Foundation module for the School Management System.

Provides the shared records every downstream school module depends on:

* Academic years and terms
* Classrooms (with grade level, section, capacity, homeroom teacher)
* Students (extends ``res.partner`` with ``is_student`` flag)
* Guardians / parents (extends ``res.partner`` with ``is_guardian`` flag)
* Teachers (extends ``hr.employee`` with ``is_teacher`` flag)

Access is governed by three groups: Reader, User, Manager — bound to the
"School Management" privilege.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "base",
        "contacts",
        "hr",
        "mail",
    ],
    "data": [
        "security/school_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/school_academic_year_views.xml",
        "views/school_academic_term_views.xml",
        "views/school_classroom_views.xml",
        "views/res_partner_views.xml",
        "views/hr_employee_views.xml",
        "views/school_menus.xml",
    ],
    "demo": [
        "demo/school_academic_year_demo.xml",
        "demo/school_teacher_demo.xml",
        "demo/school_classroom_demo.xml",
        "demo/school_student_demo.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "post_init_hook": "_grant_admin_school_manager",
}
