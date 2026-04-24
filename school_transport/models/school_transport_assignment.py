from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SchoolTransportAssignment(models.Model):
    _name = "school.transport.assignment"
    _description = "Transport Assignment"
    _order = "academic_year_id desc, student_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        tracking=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_student", "=", True)],
        index=True,
        tracking=True,
    )
    route_id = fields.Many2one(
        "school.transport.route",
        required=True,
        index=True,
        tracking=True,
    )
    academic_year_id = fields.Many2one(
        "school.academic.year",
        required=True,
        default=lambda self: self.env["school.academic.year"].search([("is_current", "=", True)], limit=1),
        tracking=True,
    )
    pickup_stop_id = fields.Many2one("school.transport.stop", string="Pickup Stop")
    dropoff_stop_id = fields.Many2one("school.transport.stop", string="Drop-off Stop")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("ended", "Ended"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    notes = fields.Char()

    _assignment_student_year_active_unique = models.Constraint(
        "EXCLUDE USING btree (student_id WITH =, academic_year_id WITH =) WHERE (state = 'active')",
        "Student already has an active transport assignment for this academic year.",
    )

    @api.depends("student_id", "route_id", "academic_year_id")
    def _compute_name(self):
        for rec in self:
            if rec.name:
                continue
            parts = []
            if rec.student_id:
                parts.append(rec.student_id.display_name)
            if rec.route_id:
                parts.append(rec.route_id.code)
            if rec.academic_year_id:
                parts.append(rec.academic_year_id.code)
            rec.name = " — ".join(parts) if parts else _("New Assignment")

    @api.constrains("pickup_stop_id", "dropoff_stop_id", "route_id")
    def _check_stops_belong_to_route(self):
        for rec in self:
            if rec.pickup_stop_id and rec.pickup_stop_id.route_id != rec.route_id:
                raise ValidationError(
                    _("Pickup stop %s is not on route %s.") % (rec.pickup_stop_id.name, rec.route_id.name)
                )
            if rec.dropoff_stop_id and rec.dropoff_stop_id.route_id != rec.route_id:
                raise ValidationError(
                    _("Drop-off stop %s is not on route %s.") % (rec.dropoff_stop_id.name, rec.route_id.name)
                )

    def action_activate(self):
        self.write({"state": "active"})

    def action_end(self):
        self.write({"state": "ended"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
