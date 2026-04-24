{
    "name": "School Library",
    "version": "19.0.1.0.0",
    "summary": "Book catalog, copy tracking, and loan lifecycle with overdue fines",
    "description": """
School Library
==============
* ``school.library.category`` / ``school.library.author`` — library taxonomy.
* ``school.library.book`` — title metadata with ISBN, authors, category.
* ``school.library.book.copy`` — physical copy tracked individually
  (``available`` / ``borrowed`` / ``lost`` / ``damaged``).
* ``school.library.loan`` — borrow transaction with automatic overdue
  detection and a fine amount computed from the configured per-day rate.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "views/school_library_category_views.xml",
        "views/school_library_author_views.xml",
        "views/school_library_book_copy_views.xml",
        "views/school_library_book_views.xml",
        "views/school_library_loan_views.xml",
        "views/school_library_menus.xml",
    ],
    "demo": [
        "demo/school_library_category_demo.xml",
        "demo/school_library_author_demo.xml",
        "demo/school_library_book_demo.xml",
        "demo/school_library_loan_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
