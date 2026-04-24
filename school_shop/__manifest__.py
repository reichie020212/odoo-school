{
    "name": "School Shop",
    "version": "19.0.1.0.0",
    "summary": "Uniforms, textbooks, and supplies with stock-backed inventory and direct sales",
    "description": """
School Shop
===========
* Shop products are Odoo products flagged with ``is_school_shop_item``.
  Storable products track inventory through Odoo's stock module.
* ``school.shop.sale`` is a minimal sales record (buyer + lines + total +
  state). Confirming a sale creates and validates an outgoing
  ``stock.picking`` so inventory is decremented via Odoo's standard
  stock machinery.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_base",
        "product",
        "stock",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/school_shop_sale_views.xml",
        "views/school_shop_menus.xml",
    ],
    "demo": [
        "demo/product_template_demo.xml",
        "demo/school_shop_sale_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
