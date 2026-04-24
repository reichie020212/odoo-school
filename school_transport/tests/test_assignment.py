from datetime import date

import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestTransportAssignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Assignment = cls.env["school.transport.assignment"]
        cls.Route = cls.env["school.transport.route"]
        cls.Stop = cls.env["school.transport.stop"]
        cls.Partner = cls.env["res.partner"]
        Year = cls.env["school.academic.year"]

        cls.year = Year.create(
            {
                "name": "Asg 2099",
                "code": "AS99",
                "date_start": date(2099, 8, 1),
                "date_end": date(2100, 5, 31),
            }
        )
        cls.route_a = cls.Route.create({"code": "RT-A", "name": "Route A"})
        cls.route_b = cls.Route.create({"code": "RT-B", "name": "Route B"})
        cls.stop_a1 = cls.Stop.create({"route_id": cls.route_a.id, "name": "A1"})
        cls.stop_a2 = cls.Stop.create({"route_id": cls.route_a.id, "name": "A2"})
        cls.stop_b1 = cls.Stop.create({"route_id": cls.route_b.id, "name": "B1"})
        cls.student = cls.Partner.create({"name": "Asg Student", "is_student": True})
        cls.student2 = cls.Partner.create({"name": "Asg Student 2", "is_student": True})

    def _make_assignment(self, **overrides):
        defaults = {
            "student_id": self.student.id,
            "route_id": self.route_a.id,
            "academic_year_id": self.year.id,
        }
        defaults.update(overrides)
        return self.Assignment.create(defaults)

    def test_create_assignment(self):
        a = self._make_assignment()
        self.assertEqual(a.state, "draft")

    def test_stop_must_belong_to_route(self):
        with self.assertRaises(ValidationError):
            self._make_assignment(pickup_stop_id=self.stop_b1.id)

    def test_stop_from_own_route_ok(self):
        a = self._make_assignment(pickup_stop_id=self.stop_a1.id, dropoff_stop_id=self.stop_a2.id)
        self.assertEqual(a.pickup_stop_id, self.stop_a1)

    @mute_logger("odoo.sql_db")
    def test_one_active_per_student_per_year(self):
        a1 = self._make_assignment()
        a1.action_activate()
        a2 = self._make_assignment(route_id=self.route_b.id)
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            a2.action_activate()
            self.env.flush_all()

    def test_two_students_same_route_ok(self):
        a1 = self._make_assignment()
        a1.action_activate()
        a2 = self._make_assignment(student_id=self.student2.id)
        a2.action_activate()
        self.assertEqual(a2.state, "active")

    def test_lifecycle(self):
        a = self._make_assignment()
        a.action_activate()
        self.assertEqual(a.state, "active")
        a.action_end()
        self.assertEqual(a.state, "ended")
        a.action_reset_to_draft()
        self.assertEqual(a.state, "draft")
