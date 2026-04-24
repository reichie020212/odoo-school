import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestCanteenWallet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wallet = cls.env["school.canteen.wallet"]
        cls.Partner = cls.env["res.partner"]
        cls.student = cls.Partner.create({"name": "Wallet Test Student", "is_student": True})

    def test_create_wallet(self):
        w = self.Wallet.create({"student_id": self.student.id})
        self.assertEqual(w.balance, 0.0)
        self.assertEqual(w.state, "active")

    @mute_logger("odoo.sql_db")
    def test_student_unique(self):
        self.Wallet.create({"student_id": self.student.id})
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self.Wallet.create({"student_id": self.student.id})
            self.env.flush_all()

    def test_freeze_unfreeze(self):
        w = self.Wallet.create({"student_id": self.student.id})
        w.action_freeze()
        self.assertEqual(w.state, "frozen")
        w.action_unfreeze()
        self.assertEqual(w.state, "active")
