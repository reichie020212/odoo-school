# `school_canteen` — Entity Relationship Diagram

```mermaid
erDiagram
    PRODUCT_TEMPLATE }o--o{ SCHOOL_CANTEEN_DIETARY_TAG : "canteen_dietary_tag_ids"
    RES_PARTNER }o--o{ SCHOOL_CANTEEN_DIETARY_TAG : "canteen_allergy_tag_ids"
    SCHOOL_CANTEEN_MENU }o--o{ PRODUCT_TEMPLATE : "item_ids (M:N)"
    SCHOOL_CANTEEN_WALLET }o--|| RES_PARTNER : "student_id (unique)"
    SCHOOL_CANTEEN_WALLET ||--o{ SCHOOL_CANTEEN_TRANSACTION : "transaction_ids"
    SCHOOL_CANTEEN_TRANSACTION }o--o{ PRODUCT_TEMPLATE : "item_ids (purchase)"

    SCHOOL_CANTEEN_DIETARY_TAG {
        char name
        char code "unique"
        char description
        integer color
        boolean active
    }

    PRODUCT_TEMPLATE {
        boolean is_canteen_item
        many2many canteen_dietary_tag_ids "what the item contains"
    }

    RES_PARTNER {
        many2many canteen_allergy_tag_ids "what the student is allergic to"
    }

    SCHOOL_CANTEEN_MENU {
        char name "computed"
        date date
        selection state "draft / published / closed"
        many2many item_ids "canteen products"
        integer item_count "computed, stored"
    }

    SCHOOL_CANTEEN_WALLET {
        char name "computed"
        many2one student_id "unique, is_student=True"
        monetary balance "stored, updated on post/cancel"
        monetary topup_total "computed"
        monetary purchase_total "computed"
        selection state "active / frozen"
    }

    SCHOOL_CANTEEN_TRANSACTION {
        char name "computed"
        many2one wallet_id "cascade"
        many2one student_id "related from wallet, stored"
        selection type "topup / purchase"
        date date
        monetary amount "purchase computes from items"
        many2many item_ids "purchase only"
        selection method "cash / bank / card / other"
        char description
        selection state "draft / posted / cancelled"
        datetime posted_at
    }
```

## Notes

- **Same dietary tag model is reused on both sides** — item has `canteen_dietary_tag_ids` (what it contains) and student has `canteen_allergy_tag_ids` (what they're allergic to). Purchase validation intersects the two sets; any overlap blocks the post with a ValidationError.
- **Wallet balance is stored** and explicitly adjusted inside `action_post` / `action_cancel`. The `topup_total` / `purchase_total` / `transaction_count` fields are computed from posted transactions for display.
- **Single-record per student** enforced by `UNIQUE(student_id)` on the wallet.
- **Transaction constraints** — positive amount (`@api.constrains`), wallet must be active when posting (UserError), sufficient balance on purchase (UserError), and the allergy-intersection rule (ValidationError). Cancelling a posted transaction reverses its balance effect.
- **No menu coupling** — purchases don't have to be from today's `school.canteen.menu`. The menu is a display roster for students/staff, not a hard gate.
```
