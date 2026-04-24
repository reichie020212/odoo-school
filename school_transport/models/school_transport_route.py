from odoo import api, fields, models


class SchoolTransportRoute(models.Model):
    _name = "school.transport.route"
    _description = "Transport Route"
    _order = "code"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    vehicle_id = fields.Many2one(
        "school.transport.vehicle",
        tracking=True,
    )
    stop_ids = fields.One2many("school.transport.stop", "route_id", string="Stops")
    assignment_ids = fields.One2many(
        "school.transport.assignment",
        "route_id",
        string="Assignments",
    )
    stop_count = fields.Integer(compute="_compute_counts", store=True)
    assignment_count = fields.Integer(compute="_compute_counts", store=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    _route_code_unique = models.Constraint(
        "UNIQUE(code)",
        "Route code must be unique.",
    )

    @api.depends("stop_ids", "assignment_ids", "assignment_ids.state")
    def _compute_counts(self):
        for rec in self:
            rec.stop_count = len(rec.stop_ids)
            rec.assignment_count = sum(1 for a in rec.assignment_ids if a.state == "active")

    def action_activate(self):
        self.write({"state": "active"})

    def action_deactivate(self):
        self.write({"state": "inactive"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
