{
    "name": "School Fees",
    "version": "19.0.1.0.0",
    "summary": "Fee items, fee structures, per-student enrollments, and scholarships",
    "description": """
School Fees
===========
Finance layer for the School Management System:

* Fee items as Odoo services (``product.template`` extended with
  ``is_school_fee``).
* ``school.fee.structure`` bundles items for a grade level + term.
* ``school.fee.enrollment`` attaches a structure to a student and generates
  a customer invoice (``account.move``).
* ``school.scholarship`` applies fixed-amount or percentage discounts to an
  enrollment; the generated invoice reflects the discounts as negative
  lines.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_base",
        "account",
        "product",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/school_fee_structure_views.xml",
        "views/school_scholarship_views.xml",
        "views/school_fee_enrollment_views.xml",
        "views/school_fees_menus.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/school_fee_structure_demo.xml",
        "demo/school_fee_enrollment_demo.xml",
        "demo/school_scholarship_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
