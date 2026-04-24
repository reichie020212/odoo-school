{
    "name": "School Portal",
    "version": "19.0.1.0.0",
    "summary": "Student / guardian self-service dashboard on Odoo's portal",
    "description": """
School Portal
=============
Adds a ``/my/school`` dashboard to Odoo's portal. Portal users (students
or guardians) see their school-related records — report cards, exam
results, fee enrollments — in one page.

* Extends the portal home with school-section cards.
* Ships record rules so portal users only see their own records.
* Pulls data from ``school_academics``, ``school_exams``, and ``school_fees``.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "portal",
        "school_base",
        "school_academics",
        "school_exams",
        "school_fees",
    ],
    "data": [
        "security/school_portal_security.xml",
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
