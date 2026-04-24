# School Fees

**Odoo 19 Community module — fee structures, per-student enrollments, and scholarships for the School Management System.**

Depends on `school_base` and Odoo's `account` / `product` / `mail` modules.

## Purpose

Turns the academic records from `school_base` into customer invoices:

- Fee items are Odoo services (`product.template` with `is_school_fee=True`), so Odoo's pricing, taxes, analytic tracking, and accounts work out of the box.
- A `school.fee.structure` bundles items for a grade level + term.
- A `school.fee.enrollment` attaches a structure to a student, rolls up totals (including scholarship discounts), and generates a customer invoice.
- `school.scholarship` records apply fixed-amount or percentage discounts to an enrollment and flow through as negative lines on the generated invoice.

## What this module provides

### Models

| Model | Summary |
|---|---|
| `product.template` (extended) | `is_school_fee` flag — marks a product as a school fee item. |
| `school.fee.structure` | Named bundle for a `grade_level × term`, with `line_ids` and a rolled-up `total_amount`. Unique per code and per `(grade_level, term)`. |
| `school.fee.structure.line` | Fee item line: product + quantity + price_unit + subtotal. |
| `school.fee.enrollment` | Per-student enrollment on a structure; draft → confirmed → invoiced → paid (via invoice state). Unique per `(student, structure)`. Rejects grade mismatches between student's classroom and structure. |
| `school.scholarship` | Discount record attached to an enrollment. Either fixed `amount` OR `percentage` (XOR, Python constraint). Applied scholarships deduct from enrollment totals and appear as negative lines on the invoice. |
| `account.move` (extended) | `school_enrollment_ids` one2many inverse — lets us filter customer invoices that originated from a fee enrollment. |

### Invoicing

Pressing **Generate Invoice** on a draft or confirmed enrollment creates an `account.move` with:

- `move_type = "out_invoice"`, `partner_id = student`, `invoice_origin = enrollment.display_name`.
- One positive line per `school.fee.structure.line`.
- One negative line per **applied** scholarship, labelled `Scholarship: <name>` with `price_unit = -computed_amount`.
- Guardians of the student are automatically subscribed as followers so they receive invoice notifications via chatter.

The invoice is left in draft for Accounting to review and post. Once posted, the enrollment's `amount_paid` / `amount_due` and `payment_state` mirror the invoice. If a change is needed after invoicing (add scholarship, correct amount), cancel the invoice via **Cancel** on the enrollment, reset to draft, and regenerate — Odoo's accounting integrity rules make post-hoc invoice edits painful, so we don't try.

### Menus

- **School → Finance → Fee Enrollments / Fee Invoices / Scholarships**
- **School → Configuration → Fee Structures / Fee Items** (manager only)

Fee items use a pre-filtered `product.template` list with `is_school_fee=True`, and the form adds an `Is School Fee` toggle next to the price.

### Security

Reuses `school_base`'s Reader / User / Manager groups:

- **Reader** — read-only on all new records.
- **User** — create/read/write enrollments and scholarships; read-only on structures and fee items (managed by admins).
- **Manager** — full CRUD including structure and fee item management.

## Dependencies

- `school_base`
- `account`
- `product`
- `mail`

## Installation

```bash
odoo-bin -d school_dev -i school_fees
```

## Demo data

Loaded when "Demo Data" is enabled:

- 3 fee item products — Tuition (₱50,000), Lab Fee (₱5,000), Activity Fee (₱2,000).
- 2 open fee structures — Grade 9 S1 2026-2027 (₱57,000 total) and Grade 10 S1 2026-2027 (₱62,000).
- 2 draft enrollments — Alice Garcia (9A) and Ben Garcia (10A).
- 1 applied scholarship — Alice gets a 10% Merit Scholarship (₱5,700 off).

Running **Generate Invoice** on Alice's enrollment produces a customer invoice with 3 fee lines + 1 negative scholarship line totalling ₱51,300.

## Tests

```bash
odoo-bin -d school_dev -i school_fees --test-enable --test-tags=/school_fees --stop-after-init
```

Covers:

- Product flag behaviour and filtering.
- Fee structure name autocompute, unique code, unique (grade, term), total rollup.
- Enrollment uniqueness, grade/structure match enforcement, invoice generation, negative scholarship line, idempotency guard, cancel flow, guardian subscription, state lifecycle.
- Scholarship XOR constraint (amount vs percentage), percentage bounds, computed amount, state lifecycle.
