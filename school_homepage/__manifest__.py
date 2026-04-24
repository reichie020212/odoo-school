{
    "name": "School Homepage",
    "version": "19.0.1.0.0",
    "summary": "Website-editable landing page at / for the School Management System",
    "description": """
School Homepage
===============
Ships a website-editable landing page at ``/`` that introduces the
school. Reuses Odoo's ``website`` module entirely so non-devs can
edit copy, hero image, and blocks via the Website builder.

Content:
* School identity (company name + logo).
* Quick stats pulled from ``school_base`` + other installed school_*
  modules (students, teachers, classrooms, courses, books).
* Call-to-action buttons to /my (portal) and /web (backend).
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "website",
        "school_base",
        "school_academics",
        "school_exams",
        "school_fees",
        "school_library",
        "school_canteen",
        "school_shop",
        "school_transport",
        "school_portal",
        "school_comms",
    ],
    "data": [
        "views/homepage_template.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
