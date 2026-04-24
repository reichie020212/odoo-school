# School Library

**Odoo 19 Community module — book catalog, physical-copy tracking, and loan lifecycle for the School Management System.**

Depends on `school_base`. Fines are computed on the loan record using a per-day rate from `ir.config_parameter`; integration with `school_fees` for auto-invoicing is deferred to a future module.

## Models

| Model | Summary |
|---|---|
| `school.library.category` | Simple taxonomy (Fiction, Science, History…). |
| `school.library.author` | Author record (name, bio, archive flag). |
| `school.library.book` | Title with ISBN, authors (m2m), category, publisher, and copy rollups. |
| `school.library.book.copy` | Physical copy with unique barcode and state (`available` / `borrowed` / `lost` / `damaged`). |
| `school.library.loan` | Borrow transaction: book_copy + borrower + borrow_date + due_date + return_date + state + computed fine. |

## Loan lifecycle

`draft` → **Confirm Borrow** → `borrowed` (copy state = `borrowed`) → **Mark Returned** → `returned` (on time) or `returned_late` (past due) → copy state back to `available`. **Mark Lost** from `draft`/`borrowed` sets both loan and copy to `lost`.

Fine is computed on the fly:

- While `borrowed`: `overdue_days = max(0, today − due_date)`, `fine_amount = overdue_days × fine_per_day`.
- While `returned_late`: `overdue_days = return_date − due_date`, same fine formula.
- Otherwise 0.

## Configuration

Two `ir.config_parameter` keys (seeded with defaults, editable in Settings > Technical):

- `school_library.loan_period_days` — default **14**. Used to auto-compute due date when creating a loan.
- `school_library.fine_per_day` — default **5.0**. Used to compute `fine_amount` on overdue loans.

## Menus

- **School → Library → Books / Copies / Loans**
- **School → Configuration → Library Categories / Library Authors**

## Security

Reuses `school_base`'s Reader / User / Manager groups. User can create/update loans; Manager manages catalog + config.

## Demo data

- 3 categories (Fiction, Science, History), 3 authors, 3 books × 2 copies each (6 copies total).
- 1 active loan: Alice Garcia has Harry Potter copy #1 out (due 2026-08-29).
- 1 completed loan: Ben Garcia returned Cosmos copy #1 on time.

## Tests

```bash
odoo-bin -d school_dev -i school_library --test-enable --test-tags=/school_library --stop-after-init
```

Covers: barcode + ISBN uniqueness, copy counts, loan state machine, copy/loan state sync, date constraints, double-borrow prevention, fine calculation for late returns, lost flow, config param reads.
