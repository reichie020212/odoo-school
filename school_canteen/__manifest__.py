{
    "name": "School Canteen",
    "version": "19.0.1.0.0",
    "summary": "Canteen items, daily menus, prepaid student wallets, and allergy-aware purchases",
    "description": """
School Canteen
==============
* Canteen items are Odoo products flagged with ``is_canteen_item`` and
  tagged with ``school.canteen.dietary.tag`` records.
* Students have allergy tags on ``res.partner`` — a purchase is blocked
  when the student's allergies intersect the items' dietary tags.
* ``school.canteen.wallet`` tracks a per-student prepaid balance.
* ``school.canteen.transaction`` unifies top-ups and purchases with a
  draft → posted → cancelled lifecycle; posting a transaction adjusts
  the wallet balance, cancelling reverses it.
* ``school.canteen.menu`` holds daily menu rosters.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_base",
        "product",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/school_canteen_dietary_tag_views.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/school_canteen_menu_views.xml",
        "views/school_canteen_wallet_views.xml",
        "views/school_canteen_transaction_views.xml",
        "views/school_canteen_menus.xml",
    ],
    "demo": [
        "demo/school_canteen_dietary_tag_demo.xml",
        "demo/product_template_demo.xml",
        "demo/res_partner_demo.xml",
        "demo/school_canteen_menu_demo.xml",
        "demo/school_canteen_wallet_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
