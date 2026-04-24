# odoo-school

**School Management System for Odoo 19 Community Edition** — a suite of 11 custom addon modules covering the full student lifecycle from admissions through graduation, billing, library loans, canteen purchases, transport, and parent self-service.

## Architecture

Each module is a sibling directory at the repo root with its own `__manifest__.py` and `__init__.py`. The suite layers cleanly — each module only depends on the ones directly below it plus Odoo CE base modules:

```
school_homepage  (website-based landing page at /)
      │
      ├── school_portal       (student/guardian dashboard at /my/school)
      ├── school_comms        (mail templates + automation rules)
      ├── school_transport    (vehicles, routes, stops, assignments)
      ├── school_shop         (uniforms/books inventory with stock integration)
      ├── school_canteen      (menus, prepaid wallets, allergy-aware purchases)
      ├── school_library      (catalog, copies, loans, overdue fines)
      ├── school_fees         (fee structures, enrollments, scholarships, invoices)
      ├── school_exams        (grading scales, exams, results, PDF report cards)
      └── school_academics    (subjects, courses, sessions, attendance)
              │
              └── school_base (academic years, terms, classrooms, students,
                               guardians, teachers)
```

## Modules

| Module | Purpose |
|---|---|
| [`school_base`](./school_base/README.md) | Foundation: academic years, terms, classrooms (K–12), students (extends `res.partner` with `is_student`), guardians (`is_guardian`), and teachers (extends `hr.employee` with `is_teacher`). Security privilege + 3 groups (Reader / User / Manager). |
| [`school_academics`](./school_academics/README.md) | Curriculum catalog (`school.subject`), course offerings (subject × term × classroom × teacher with auto-enrolled students), weekly schedule rules that materialise `calendar.event` sessions, per-session student attendance with "Mark All Present". |
| [`school_exams`](./school_exams/README.md) | Configurable grading scales (US A–F, Philippine DepEd, or custom) with bands → letter + GPA, exam types with default weights, exams tied to courses, student results with computed percentage/letter/GPA, per-term report cards with weighted course grades and a QWeb PDF. |
| [`school_fees`](./school_fees/README.md) | Fee items as products (`is_school_fee` flag), fee structures per grade × term, per-student enrollments with fixed-amount / percentage scholarships, invoice generation against Odoo's `account.move`. |
| [`school_library`](./school_library/README.md) | Catalog (categories, authors, books) with per-copy tracking (unique barcode, state), loan lifecycle (draft → borrowed → returned / returned_late / lost), auto-computed overdue days and fine amount from `ir.config_parameter` rate. |
| [`school_canteen`](./school_canteen/README.md) | Dietary tags shared between item contents and student allergies, per-student prepaid wallets (unique on student), unified transaction model (topup / purchase) with state lifecycle that adjusts the wallet balance. |
| [`school_shop`](./school_shop/README.md) | Uniforms, textbooks, supplies as Odoo products (`is_school_shop_item`); sales records with line items; storable items trigger `stock.picking` creation on sale confirm. |
| [`school_transport`](./school_transport/README.md) | Vehicles (plate, driver, capacity), routes with ordered stops, per-student assignments scoped to academic year (PostgreSQL partial unique constraint enforces one active assignment per year). |
| [`school_portal`](./school_portal/README.md) | `/my/school` dashboard for students and guardians showing report cards, recent exam results, outstanding fees. Record rules scope visibility to the portal user's own data or their wards. |
| [`school_comms`](./school_comms/README.md) | Mail templates for fee-invoice-ready / report-card-final / exam-published, plus `base.automation` rules that fire on state transitions and post the templates as chatter messages. |
| [`school_homepage`](./school_homepage/README.md) | Website-based landing page at `/` with school identity, live stats (students/teachers/classrooms/courses/books), and portal/backend call-to-action buttons. Editable via the Odoo Website builder. |

**145 tests across the suite**, 0 failures on Odoo 19 CE.

## Quick start

The repo ships a Docker Compose stack (Odoo 19 CE + PostgreSQL 16).

```bash
# One-time: create a .env with a dev password for Postgres (gitignored)
echo 'POSTGRES_PASSWORD=odoo-dev-password' > .env

# Bring up db + odoo
docker compose up -d

# Install the full suite (pulls in dependencies in order)
docker compose exec odoo odoo -d school_dev -i school_homepage --stop-after-init --without-demo=False

# Open the public homepage
open http://localhost:8069/

# Or the backend (admin / admin by default in dev)
open http://localhost:8069/web
```

Installing `school_homepage` pulls in every other module transitively. To install a subset, pick a different `-i <module>`.

## Running tests

Tests are run via Odoo's own test harness, not pytest:

```bash
# Single module
docker compose run --rm --no-deps odoo odoo \
    -d test_db -i school_exams --test-enable \
    --test-tags=/school_exams --stop-after-init

# All school modules
docker compose run --rm --no-deps odoo odoo \
    -d test_db -i school_homepage --test-enable \
    --test-tags=/school_base,/school_academics,/school_exams,/school_fees,/school_library,/school_canteen,/school_shop,/school_transport,/school_portal,/school_comms,/school_homepage \
    --stop-after-init
```

## Development tooling

- **Python 3.12** (pinned in `.python-version`), Odoo 19 CE on `odoo:19.0`.
- **`uv`** for the Python environment (`uv.lock` committed) — run `uv sync` not `pip install`.
- **`ruff`** (line length 120, target 3.12) — `uv run ruff check . --fix && uv run ruff format .`.
- **`pre-commit`** hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-xml, check-added-large-files, ruff, ruff-format.
- Commits are **SSH-signed** (`git commit -s -S`) with no self-attribution in the message.

## Documentation layout

- `README.md` (this file) — top-level overview.
- `<module>/README.md` — one per module, purpose + models + dependencies + tests.
- `docs/guide/<module>-erd.md` — one Mermaid ERD per module, committed.
- `docs/plan/<thing>-blueprint.md` — design notes and implementation blueprints, **gitignored**.
- [`CLAUDE.md`](./CLAUDE.md) — operating rules for Claude Code when working on this repo.
- [`GEMINI.md`](./GEMINI.md) — operating rules for Gemini when designing blueprints for this repo.

## Division of labor

Work on this project is split between Gemini (Architect — high-level design, model schemas, tricky business logic, assets) and Claude Code (Executor — writing boilerplate, running tooling, committing code). Red consults Gemini for a Blueprint, hands it to Claude for execution, and Claude re-consults Gemini mid-execution when it hits a design-level blocker. The full rules live in `CLAUDE.md` and `GEMINI.md`.

## License

LGPL-3 (same as Odoo Community Edition).
