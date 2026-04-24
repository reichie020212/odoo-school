{
    "name": "School Transport",
    "version": "19.0.1.0.0",
    "summary": "Buses, routes, stops, and per-student transport assignments",
    "description": """
School Transport
================
* ``school.transport.vehicle`` — bus records (plate, model, capacity,
  driver, state).
* ``school.transport.route`` — named route with ordered stops and an
  assigned vehicle.
* ``school.transport.stop`` — stop on a route with a pickup time.
* ``school.transport.assignment`` — student ↔ route link with pickup and
  drop-off stops; one active assignment per student per academic year.
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
        "views/school_transport_vehicle_views.xml",
        "views/school_transport_stop_views.xml",
        "views/school_transport_route_views.xml",
        "views/school_transport_assignment_views.xml",
        "views/school_transport_menus.xml",
    ],
    "demo": [
        "demo/school_transport_vehicle_demo.xml",
        "demo/school_transport_route_demo.xml",
        "demo/school_transport_assignment_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
