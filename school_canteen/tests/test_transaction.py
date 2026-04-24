from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestCanteenTransaction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wallet = cls.env["school.canteen.wallet"]
        cls.Tx = cls.env["school.canteen.transaction"]
        cls.Product = cls.env["product.product"]
        cls.Tag = cls.env["school.canteen.dietary.tag"]
        cls.Partner = cls.env["res.partner"]

        cls.tag_nuts = cls.Tag.create({"name": "Nuts", "code": "tst_nuts"})
        cls.tag_gluten = cls.Tag.create({"name": "Gluten", "code": "tst_gluten"})

        cls.student = cls.Partner.create(
            {
                "name": "Tx Student",
                "is_student": True,
                "canteen_allergy_tag_ids": [(6, 0, [cls.tag_nuts.id])],
            }
        )
        cls.other = cls.Partner.create({"name": "Tx Other", "is_student": True})

        cls.wallet = cls.Wallet.create({"student_id": cls.student.id})
        cls.wallet_other = cls.Wallet.create({"student_id": cls.other.id})

        cls.safe_item = cls.Product.create(
            {"name": "Rice Bowl", "type": "consu", "is_canteen_item": True, "list_price": 50.0}
        )
        cls.gluten_item = cls.Product.create(
            {
                "name": "Sandwich",
                "type": "consu",
                "is_canteen_item": True,
                "list_price": 40.0,
                "canteen_dietary_tag_ids": [(6, 0, [cls.tag_gluten.id])],
            }
        )
        cls.nut_item = cls.Product.create(
            {
                "name": "PB Cookie",
                "type": "consu",
                "is_canteen_item": True,
                "list_price": 20.0,
                "canteen_dietary_tag_ids": [(6, 0, [cls.tag_nuts.id])],
            }
        )

    def test_topup_increases_balance(self):
        tx = self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 200.0})
        tx.action_post()
        self.assertEqual(tx.state, "posted")
        self.assertEqual(self.wallet.balance, 200.0)

    def test_purchase_decreases_balance(self):
        self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 500.0}).action_post()
        tx = self.Tx.create(
            {
                "wallet_id": self.wallet.id,
                "type": "purchase",
                "item_ids": [(6, 0, [self.safe_item.id])],
            }
        )
        self.assertEqual(tx.amount, 50.0)
        tx.action_post()
        self.assertEqual(self.wallet.balance, 450.0)

    def test_insufficient_balance_blocks_purchase(self):
        tx = self.Tx.create(
            {
                "wallet_id": self.wallet.id,
                "type": "purchase",
                "item_ids": [(6, 0, [self.safe_item.id])],
            }
        )
        with self.assertRaises(UserError):
            tx.action_post()

    def test_allergy_blocks_purchase(self):
        self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 500.0}).action_post()
        with self.assertRaises(ValidationError):
            self.Tx.create(
                {
                    "wallet_id": self.wallet.id,
                    "type": "purchase",
                    "item_ids": [(6, 0, [self.nut_item.id])],
                }
            )

    def test_cancel_reverses_balance(self):
        tx = self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 300.0})
        tx.action_post()
        self.assertEqual(self.wallet.balance, 300.0)
        tx.action_cancel()
        self.assertEqual(tx.state, "cancelled")
        self.assertEqual(self.wallet.balance, 0.0)

    def test_cannot_post_on_frozen_wallet(self):
        self.wallet.action_freeze()
        tx = self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 50.0})
        with self.assertRaises(UserError):
            tx.action_post()

    def test_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.Tx.create({"wallet_id": self.wallet.id, "type": "topup", "amount": 0})

    def test_non_allergic_purchase_proceeds(self):
        # The "other" student has no allergies; gluten item should pass.
        self.Tx.create({"wallet_id": self.wallet_other.id, "type": "topup", "amount": 100.0}).action_post()
        tx = self.Tx.create(
            {
                "wallet_id": self.wallet_other.id,
                "type": "purchase",
                "item_ids": [(6, 0, [self.gluten_item.id])],
            }
        )
        tx.action_post()
        self.assertEqual(tx.state, "posted")
        self.assertEqual(self.wallet_other.balance, 60.0)
