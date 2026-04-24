from odoo import fields, models


class SchoolTransportVehicle(models.Model):
    _name = "school.transport.vehicle"
    _description = "Transport Vehicle"
    _order = "plate_number"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    plate_number = fields.Char(required=True, tracking=True, index=True)
    model = fields.Char(tracking=True)
    capacity = fields.Integer(default=30, help="Maximum student capacity.")
    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("active", "Active"),
            ("in_repair", "In Repair"),
            ("retired", "Retired"),
        ],
        default="active",
        required=True,
        tracking=True,
    )
    route_ids = fields.One2many("school.transport.route", "vehicle_id", string="Routes")
    notes = fields.Text()
    active = fields.Boolean(default=True)

    _vehicle_plate_unique = models.Constraint(
        "UNIQUE(plate_number)",
        "Plate number must be unique.",
    )

    def _compute_name(self):
        for rec in self:
            if rec.name:
                continue
            parts = []
            if rec.plate_number:
                parts.append(rec.plate_number)
            if rec.model:
                parts.append(rec.model)
            rec.name = " — ".join(parts) if parts else "New Vehicle"
