{
    "name": "School Exams",
    "version": "19.0.1.0.0",
    "summary": "Exam types, exams, results, and term report cards",
    "description": """
School Exams
============
Assessment lifecycle for the School Management System:

* Configurable grading scales (US A-F, Philippine DepEd, custom).
* Exam types with default weights (Quiz, Midterm, Final, ...).
* Exams per course with per-exam weight and max score.
* Student exam results with computed percentage, letter grade, and GPA.
* Term report cards with weighted course grades and overall GPA.
* QWeb PDF report card template.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_academics",
        "school_base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/school_grading_scale_views.xml",
        "views/school_exam_type_views.xml",
        "views/school_exam_views.xml",
        "views/school_exam_result_views.xml",
        "views/school_report_card_views.xml",
        "report/school_report_card_templates.xml",
        "report/school_report_card_actions.xml",
        "views/school_exams_menus.xml",
    ],
    "demo": [
        "demo/school_grading_scale_demo.xml",
        "demo/school_exam_type_demo.xml",
        "demo/school_exam_demo.xml",
        "demo/school_exam_result_demo.xml",
        "demo/school_report_card_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
