{
    "name": "School Communications",
    "version": "19.0.1.0.0",
    "summary": "Mail templates and automated notifications for school events",
    "description": """
School Communications
=====================
Ships ready-to-use mail templates and ``base.automation`` rules for
common school events:

* Fee invoice ready — sent to student (+ guardian followers) when a
  school.fee.enrollment transitions to the 'invoiced' state.
* Report card finalized — sent to student (+ guardians) when a
  school.report.card transitions to 'final'.
* Exam published — sent to enrolled students when a school.exam
  transitions to 'published'.

Admins can duplicate and tweak these templates from Technical → Email →
Email Templates.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "mail",
        "base_automation",
        "school_base",
        "school_academics",
        "school_exams",
        "school_fees",
    ],
    "data": [
        "data/mail_templates.xml",
        "data/base_automations.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
