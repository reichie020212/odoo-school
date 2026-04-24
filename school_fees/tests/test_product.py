from odoo.tests.common import TransactionCase


class TestProductFeeFlag(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"]

    def test_flag_defaults_false(self):
        p = self.Product.create({"name": "Non-fee Product", "type": "service"})
        self.assertFalse(p.is_school_fee)

    def test_flag_propagates_to_template(self):
        p = self.Product.create({"name": "Tuition X", "type": "service", "is_school_fee": True})
        self.assertTrue(p.product_tmpl_id.is_school_fee)

    def test_fee_filter_excludes_non_fees(self):
        self.Product.create({"name": "Regular Service", "type": "service"})
        fee = self.Product.create({"name": "Fee X", "type": "service", "is_school_fee": True})
        fees = self.Product.search([("is_school_fee", "=", True)])
        self.assertIn(fee, fees)
