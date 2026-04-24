from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestShopSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Sale = cls.env["school.shop.sale"]
        cls.Line = cls.env["school.shop.sale.line"]
        cls.Product = cls.env["product.product"]
        cls.Partner = cls.env["res.partner"]

        cls.buyer = cls.Partner.create({"name": "Shop Test Buyer"})
        cls.item_consu = cls.Product.create(
            {
                "name": "Shop Consu",
                "type": "consu",
                "is_school_shop_item": True,
                "list_price": 100.0,
            }
        )

    def _make_sale(self, lines=None):
        sale = self.Sale.create({"buyer_id": self.buyer.id})
        if lines is None:
            self.Line.create({"sale_id": sale.id, "product_id": self.item_consu.id, "quantity": 2, "price_unit": 100.0})
        else:
            for line in lines:
                self.Line.create({"sale_id": sale.id, **line})
        return sale

    def test_create_sale_totals(self):
        sale = self._make_sale()
        self.assertAlmostEqual(sale.total_amount, 200.0, places=2)

    def test_subtotal_per_line(self):
        sale = self._make_sale()
        line = sale.line_ids
        self.assertAlmostEqual(line.subtotal, 200.0, places=2)

    def test_cannot_confirm_empty_sale(self):
        sale = self.Sale.create({"buyer_id": self.buyer.id})
        with self.assertRaises(UserError):
            sale.action_confirm()

    def test_confirm_non_storable_skips_picking(self):
        sale = self._make_sale()
        sale.action_confirm()
        self.assertEqual(sale.state, "confirmed")
        # Pure consu (non-storable) should not produce a picking.
        self.assertFalse(sale.picking_id)

    def test_line_name_defaults_from_product(self):
        sale = self.Sale.create({"buyer_id": self.buyer.id})
        line = self.Line.create({"sale_id": sale.id, "product_id": self.item_consu.id, "quantity": 1})
        self.assertEqual(line.name, self.item_consu.display_name)
        self.assertAlmostEqual(line.price_unit, 100.0, places=2)

    def test_cancel_sale(self):
        sale = self._make_sale()
        sale.action_confirm()
        sale.action_cancel()
        self.assertEqual(sale.state, "cancelled")
