# School Canteen

**Odoo 19 Community module — daily menus, student wallets, and allergy-aware purchases.**

Depends on `school_base`, `product`, `mail`.

## Models

| Model | Summary |
|---|---|
| `school.canteen.dietary.tag` | Shared tag used for item contents and student allergies. |
| `product.template` (extended) | `is_canteen_item` + `canteen_dietary_tag_ids`. |
| `res.partner` (extended) | `canteen_allergy_tag_ids` — shown on the student info page. |
| `school.canteen.menu` | Daily menu roster (date + items + state). |
| `school.canteen.wallet` | Per-student prepaid wallet; unique on student. Balance is stored, updated on transaction post/cancel. |
| `school.canteen.transaction` | Single model for top-ups and purchases (type selection). Draft → Posted → Cancelled. |

## Flow

- **Top up:** create a transaction with `type=topup` and `amount`. **Post** adds to the wallet balance.
- **Purchase:** create a transaction with `type=purchase` and `item_ids`. Amount auto-computes from item prices. Two constraints fire on post:
  - Wallet balance must be ≥ amount (UserError otherwise).
  - Student's allergy tags must not intersect any item's dietary tags (ValidationError otherwise).
- **Cancel** a posted transaction reverses the balance change cleanly.

## Menus

- **School → Canteen → Wallets / Transactions / Daily Menus**
- **School → Configuration → Canteen Items / Dietary Tags**

## Demo data

- 3 dietary tags (Nuts, Gluten, Dairy).
- 3 canteen products (Chicken Sandwich with gluten, Rice Bowl with no allergens, Peanut Butter Cookie with nuts + gluten + dairy).
- Alice Garcia gets the Nuts allergy on her student record.
- 2 wallets (Alice ₱500, Ben ₱435) with initial posted top-ups.
- 1 posted purchase (Ben bought the Rice Bowl for ₱65).
- 1 published daily menu for 2026-08-15 with all 3 products.

## Tests

```bash
odoo-bin -d school_dev -i school_canteen --test-enable --test-tags=/school_canteen --stop-after-init
```

Covers wallet uniqueness / freeze, top-up balance change, purchase balance change, insufficient-balance block, allergy intersection block, cancel reversal, frozen-wallet post guard, positive-amount validation, and the non-allergic happy path.
