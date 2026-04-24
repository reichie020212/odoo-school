from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolTransportStop(models.Model):
    _name = "school.transport.stop"
    _description = "Transport Stop"
    _order = "route_id, sequence, pickup_time"

    route_id = fields.Many2one(
        "school.transport.route",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    pickup_time = fields.Float(
        string="Pickup Time",
        help="Time of day, 24h format. E.g. 6.5 = 06:30.",
    )
    notes = fields.Char()

    @api.constrains("pickup_time")
    def _check_pickup_time(self):
        for rec in self:
            if rec.pickup_time and not (0.0 <= rec.pickup_time < 24.0):
                raise ValidationError(_("Pickup time must be between 00:00 and 24:00."))
