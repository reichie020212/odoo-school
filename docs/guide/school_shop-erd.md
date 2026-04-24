# `school_shop` — Entity Relationship Diagram

```mermaid
erDiagram
    PRODUCT_TEMPLATE ||--o{ SCHOOL_SHOP_SALE_LINE : "product_id (is_school_shop_item=True)"
    SCHOOL_SHOP_SALE ||--o{ SCHOOL_SHOP_SALE_LINE : "line_ids"
    SCHOOL_SHOP_SALE }o--|| RES_PARTNER : "buyer_id"
    SCHOOL_SHOP_SALE }o--o| STOCK_PICKING : "picking_id (created on confirm)"

    PRODUCT_TEMPLATE {
        boolean is_school_shop_item
    }

    SCHOOL_SHOP_SALE {
        char name "computed"
        many2one buyer_id "-> res.partner"
        date date
        monetary total_amount "computed from lines"
        selection state "draft / confirmed / cancelled"
        many2one picking_id "outgoing delivery order"
        selection picking_state "related from picking"
        char note
    }

    SCHOOL_SHOP_SALE_LINE {
        many2one sale_id "cascade"
        integer sequence
        many2one product_id "-> product.product (is_school_shop_item)"
        char name "defaults from product"
        float quantity
        monetary price_unit "defaults from product.lst_price"
        monetary subtotal "computed"
    }

    STOCK_PICKING {
        selection state "driven by Odoo's standard stock flow"
    }
```

## Notes

- **Sale confirmation creates a stock.picking** (outgoing delivery) only when at least one line references a storable product and a default outgoing picking type exists. For `consu` (non-storable) lines only, the sale still confirms but no picking is generated — nothing to move through inventory. This mirrors Odoo's sale/stock integration heuristic.
- **Sale cancel cancels the picking** (unless it's already in `done` or `cancel` state). **Reset to Draft** refuses to proceed if the picking is done, otherwise cancels it and unlinks.
- **Inventory accounting** is fully delegated to Odoo's `stock` module; the sale just surfaces `picking_state` for quick visibility.
- **No `sale` module dependency.** A parallel `school.shop.sale` model stays scoped to school ops without dragging in price lists, sale teams, or the full CRM stack.
```
