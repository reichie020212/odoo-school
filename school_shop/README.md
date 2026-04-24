# School Shop

**Odoo 19 Community module — uniforms, textbooks, and supplies with stock-backed inventory and direct sales.**

Depends on `school_base`, `product`, `stock`, `mail`.

## Models

| Model | Summary |
|---|---|
| `product.template` (extended) | `is_school_shop_item` flag. Storable products (`type='product'` or `is_storable=True`) track inventory through stock. |
| `school.shop.sale` | Sales record: buyer + line_ids + total + state (draft / confirmed / cancelled). Optional linked `stock.picking`. |
| `school.shop.sale.line` | Product + quantity + price_unit + subtotal. |

## Flow

1. Admin flags shop products with `is_school_shop_item=True`.
2. Admin creates a `school.shop.sale` (buyer, date, lines).
3. **Confirm** → state becomes `confirmed`. If any line references a storable product and a default outgoing picking type exists, a `stock.picking` (delivery order) is created and assigned so inventory is reserved/moved through Odoo's standard flow.
4. Validating / posting the picking is done in Inventory — the sale surfaces `picking_state` read-only.
5. **Cancel** cancels the associated picking (if not done). **Reset to Draft** releases the picking; cannot reset a sale whose delivery is already `done`.

## Menus

- **School → Shop → Sales**
- **School → Configuration → Shop Items**

## Security

Uses `school_base` groups — Reader / User / Manager.

## Demo data

- 3 shop products: School Uniform Shirt (₱450), School Uniform Pants (₱600), Grade 9 Notebook (₱75), all storable.
- 1 draft sale: Carlos Garcia buying 3 shirts, 2 pants, and 5 notebooks for Alice (totalling ₱2,925). Left in draft so admins can manually confirm and watch a picking get created.

## Tests

```bash
odoo-bin -d school_dev -i school_shop --test-enable --test-tags=/school_shop --stop-after-init
```

Covers sale total/subtotal computation, empty-sale confirm guard, non-storable product skips picking creation (sale still confirms), line name/price defaults from product, and cancel lifecycle.
