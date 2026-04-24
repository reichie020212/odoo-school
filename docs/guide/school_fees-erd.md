# `school_fees` — Entity Relationship Diagram

```mermaid
erDiagram
    PRODUCT_TEMPLATE ||--o{ SCHOOL_FEE_STRUCTURE_LINE : "product_id (is_school_fee=True)"
    SCHOOL_FEE_STRUCTURE ||--o{ SCHOOL_FEE_STRUCTURE_LINE : "line_ids"
    SCHOOL_FEE_STRUCTURE }o--|| SCHOOL_ACADEMIC_TERM : "term_id"
    SCHOOL_FEE_ENROLLMENT }o--|| RES_PARTNER : "student_id (is_student)"
    SCHOOL_FEE_ENROLLMENT }o--|| SCHOOL_FEE_STRUCTURE : "structure_id"
    SCHOOL_FEE_ENROLLMENT ||--o{ SCHOOL_SCHOLARSHIP : "scholarship_ids"
    SCHOOL_FEE_ENROLLMENT }o--o| ACCOUNT_MOVE : "invoice_id (set null on cancel)"

    PRODUCT_TEMPLATE {
        boolean is_school_fee "flag: service used as a school fee item"
    }

    SCHOOL_FEE_STRUCTURE {
        char name "computed, editable"
        char code "unique"
        selection grade_level "K-12"
        many2one term_id
        many2one academic_year_id "related, stored"
        monetary total_amount "computed, stored"
        many2one currency_id
        selection state "draft / open / closed"
        boolean active
    }

    SCHOOL_FEE_STRUCTURE_LINE {
        many2one structure_id "cascade"
        integer sequence
        many2one product_id "-> product.product (is_school_fee)"
        char name "computed from product, editable"
        float quantity
        monetary price_unit "seeded from product.list_price"
        monetary subtotal "computed, stored"
    }

    SCHOOL_FEE_ENROLLMENT {
        char name "computed"
        many2one student_id "-> res.partner (is_student)"
        many2one structure_id
        many2one classroom_id "related from student"
        many2one term_id "related from structure, stored"
        monetary structure_total "related from structure"
        monetary scholarship_total "computed from applied scholarships"
        monetary amount_total "structure_total - scholarship_total"
        monetary amount_paid "from invoice"
        monetary amount_due "amount_total - amount_paid"
        many2one invoice_id "-> account.move (set null)"
        selection payment_state "related from invoice"
        selection state "draft / confirmed / invoiced / paid / cancelled"
    }

    SCHOOL_SCHOLARSHIP {
        char name
        many2one enrollment_id "cascade"
        selection discount_type "amount / percentage"
        monetary discount_amount "used when type=amount"
        float discount_percentage "used when type=percentage"
        monetary computed_amount "computed"
        text reason
        selection state "draft / applied / revoked"
    }

    ACCOUNT_MOVE {
        one2many school_enrollment_ids "inverse of invoice_id"
    }
```

## Notes

- **Fee items are Odoo products.** The `is_school_fee` flag lives on `product.template` and narrows the Configuration > Fee Items list + the fee structure line's product picker. No parallel fee-item model.
- **Grade enforcement.** A `school.fee.enrollment` rejects students whose classroom grade doesn't match the structure's grade (`@api.constrains`).
- **Scholarship XOR.** `discount_type` picks one of `amount` / `percentage`; Python constraint forbids setting the other field at the same time. Percentage must be in `(0, 100]`; amount must be `> 0`.
- **Invoice flow.** `action_generate_invoice` creates a draft `account.move` (`out_invoice`) with one line per structure line plus one negative line per applied scholarship. Guardians are auto-subscribed as followers. The invoice is NOT auto-posted — Accounting reviews + posts.
- **Regeneration.** Once invoiced, changes (new scholarship, amount correction) require **Cancel** on the enrollment (cancels the draft invoice too) + regenerate. Posted invoices must first be reset to draft in Accounting.
- **Relationship back to enrollment.** `account.move.school_enrollment_ids` is the one2many inverse of `school.fee.enrollment.invoice_id`, used by the "Fee Invoices" menu action to filter to school invoices only.
- **Unique constraints.** Structure code is globally unique; `(grade_level, term_id)` is unique; enrollment `(student_id, structure_id)` is unique. All other domain constraints are enforced via `@api.constrains`.
```
