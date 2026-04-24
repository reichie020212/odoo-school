import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestTransportRoute(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Route = cls.env["school.transport.route"]
        cls.Stop = cls.env["school.transport.stop"]
        cls.Vehicle = cls.env["school.transport.vehicle"]

    def _make_route(self, **overrides):
        defaults = {"code": "RT-TST", "name": "Test Route"}
        defaults.update(overrides)
        return self.Route.create(defaults)

    def test_create_route(self):
        r = self._make_route()
        self.assertEqual(r.state, "draft")
        self.assertEqual(r.stop_count, 0)

    @mute_logger("odoo.sql_db")
    def test_code_unique(self):
        self._make_route()
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_route(name="Dup")
            self.env.flush_all()

    def test_stop_count_updates(self):
        route = self._make_route()
        self.Stop.create(
            [{"route_id": route.id, "name": "A", "sequence": 10}, {"route_id": route.id, "name": "B", "sequence": 20}]
        )
        route.invalidate_recordset(["stop_count"])
        self.assertEqual(route.stop_count, 2)

    def test_state_transitions(self):
        r = self._make_route()
        r.action_activate()
        self.assertEqual(r.state, "active")
        r.action_deactivate()
        self.assertEqual(r.state, "inactive")
        r.action_reset_to_draft()
        self.assertEqual(r.state, "draft")

    @mute_logger("odoo.sql_db")
    def test_vehicle_plate_unique(self):
        self.Vehicle.create({"plate_number": "TST-001"})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Vehicle.create({"plate_number": "TST-001"})
            self.env.flush_all()
