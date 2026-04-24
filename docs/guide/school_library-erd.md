# `school_library` — Entity Relationship Diagram

```mermaid
erDiagram
    SCHOOL_LIBRARY_CATEGORY ||--o{ SCHOOL_LIBRARY_BOOK : "category_id"
    SCHOOL_LIBRARY_AUTHOR }o--o{ SCHOOL_LIBRARY_BOOK : "author_ids (M:N)"
    SCHOOL_LIBRARY_BOOK ||--o{ SCHOOL_LIBRARY_BOOK_COPY : "copy_ids"
    SCHOOL_LIBRARY_BOOK_COPY ||--o{ SCHOOL_LIBRARY_LOAN : "loan_ids"
    SCHOOL_LIBRARY_LOAN }o--|| RES_PARTNER : "borrower_id"

    SCHOOL_LIBRARY_CATEGORY {
        char name
        integer sequence
        char description
        boolean active
    }

    SCHOOL_LIBRARY_AUTHOR {
        char name
        text bio
        boolean active
    }

    SCHOOL_LIBRARY_BOOK {
        char title
        char isbn "unique"
        many2many author_ids
        many2one category_id
        char publisher
        date publish_date
        text summary
        integer copy_count "computed, stored"
        integer available_count "computed, stored"
        boolean active
    }

    SCHOOL_LIBRARY_BOOK_COPY {
        many2one book_id "cascade"
        char barcode "unique"
        selection state "available / borrowed / lost / damaged"
        many2one current_loan_id "computed (active loan)"
        char notes
        boolean active
    }

    SCHOOL_LIBRARY_LOAN {
        char name "computed"
        many2one book_copy_id
        many2one book_id "related from copy, stored"
        many2one borrower_id "-> res.partner"
        date borrow_date
        date due_date "computed from borrow + config period"
        date return_date
        selection state "draft / borrowed / returned / returned_late / lost"
        boolean is_overdue "computed, stored"
        integer overdue_days "computed, stored"
        monetary fine_amount "overdue_days * fine_per_day"
    }
```

## Notes

- **Catalog split** — `school.library.book` is the title record; `school.library.book.copy` is the individually-barcoded physical copy. Loans attach to a copy, so the same title can circulate many times in parallel.
- **Copy state is loan-driven** — confirming a loan flips the copy to `borrowed`; returning/marking-lost restores or transitions accordingly. The `current_loan_id` helper is computed from the copy's active loan.
- **Fine calculation** is computed on the loan from `overdue_days × fine_per_day` (config param `school_library.fine_per_day`, default 5.0). No separate fine model for MVP.
- **Due date defaults** to `borrow_date + loan_period_days` (config param, default 14). Admin can override on the loan form.
- **Constraints** — `due_date > borrow_date`, `return_date ≥ borrow_date`, a copy can only be on one `borrowed` loan at a time.
```
