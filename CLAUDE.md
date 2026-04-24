# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

School Management System for **Odoo 19 Community Edition** — a suite of 11 custom addon modules covering the full student lifecycle.

**Modules (all shipped):** Each lives at the repository root as a sibling directory with its own `__manifest__.py` and `__init__.py`.

| Module | One-line purpose |
|---|---|
| `school_base` | Foundation — academic years, terms, classrooms, students (extends `res.partner` with `is_student`), guardians, teachers (extends `hr.employee` with `is_teacher`). |
| `school_academics` | Subjects, courses (subject × term × classroom × teacher with auto-enrolled students), weekly schedule rules that materialise `calendar.event` sessions, per-session attendance. |
| `school_exams` | Configurable grading scales with letter/GPA bands, exam types, exams, student results, term report cards with weighted grades and a QWeb PDF. |
| `school_fees` | Fee items as products, fee structures per grade × term, per-student enrollments, fixed-amount / percentage scholarships, invoice generation against `account.move`. |
| `school_library` | Book catalog + per-copy tracking + loan lifecycle + computed overdue fines from `ir.config_parameter`. |
| `school_canteen` | Dietary tags shared across items and student allergies, prepaid wallets, topup/purchase transactions with allergy blocks. |
| `school_shop` | Shop products (`is_school_shop_item`) with sales records; confirming creates `stock.picking` for storable lines. |
| `school_transport` | Vehicles, routes with ordered stops, per-student assignments (one active per academic year). |
| `school_portal` | `/my/school` dashboard for students/guardians with report cards, exam results, fee enrollments; record rules scope to own/ward data. |
| `school_comms` | Mail templates and `base.automation` rules firing on fee-invoiced / report-card-final / exam-published state transitions. |
| `school_homepage` | Website-based landing page at `/` with school identity, live stats, and portal/backend CTAs. Editable via Odoo Website builder. |

Installing `school_homepage` pulls in the complete suite transitively. A root `README.md` summarises the above with install commands.

**Infrastructure:** Docker Compose (dev + prod), PostgreSQL 16, Odoo 19 Community.

The parent directory is `~/odoo/custom_addons/` in the running container, meaning this repo is mounted inside Odoo's custom addons path (`/mnt/extra-addons/odoo-school`).

## Division of Labor (Gemini ↔ Claude)

Work on this project is split between Gemini and Claude:

**Gemini — The Architect & Strategist**
- High-level planning, Odoo model/schema design, solving tricky business-logic problems (e.g. enrollment rules, tuition billing, grading logic), and generating assets (icons, UI images).
- Produces a step-by-step **Blueprint** for Claude to execute.

**Claude Code — The Executor & Mechanic**
- Writes the boilerplate (Python models, XML views, `ir.model.access.csv`), creates files, runs tools, commits the code.
- Takes the Blueprint from Gemini and implements it flawlessly into the codebase. Does not unilaterally redesign the architecture — on execution-time roadblocks, re-consult Gemini via `/ask gemini` instead of improvising.

### Execution Rules (Claude, on this project)

1. **Follow the Blueprint.** Do not invent complex business logic, add fields, or change database schemas unless explicitly instructed. Implement plans exactly as provided. If the plan is ambiguous, contradicts existing code, or looks wrong, re-consult the Architect (`/ask gemini`) — don't improvise.
2. **Respect Odoo's layout.** Create/modify/delete files as needed, but strictly maintain the standard Odoo 19 structure: `models/` for Python, `views/` for XML, `security/` for `ir.model.access.csv` and record rules, `data/` for seed data. Wire new files through `__init__.py` and list XML/CSV assets in `__manifest__.py`.
3. **Tooling is mandatory.** After writing or modifying Python, run both `uv run ruff check . --fix` and `uv run ruff format .` before committing — in that order. Fix any remaining issues manually and re-run until clean. For XML changes, pre-commit's `check-xml` validates on commit; don't skip hooks.
4. **Git protocol.** Once a component is built and lints clean, stage and commit with a descriptive, semantic commit message using a conventional-commits prefix (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`). Always sign with both `-s` and `-S` (see the Git commits section below). No self-attribution.
5. **Fail fast.** If a shell command fails with a non-obvious error, or Odoo returns a traceback you cannot resolve in one focused attempt, stop and report the error to Red with the full output so the Architect can be consulted. Do not silently retry, disable checks (`--no-verify`, commenting out tests), or hack around the error.
6. **Every change must have a test case.** Every improvement, addition, or change to a module must include corresponding Odoo test(s) covering the new/modified behaviour. Tests live in `tests/` inside each module, inherit from `odoo.tests.common.TransactionCase` (or `HttpCase` for UI/controller tests), and are wired through `tests/__init__.py`. The test file must be named `test_<feature>.py`. Run the module's tests locally before committing: `odoo-bin -d <db> -i <module> --test-enable --stop-after-init`. Do not skip or weaken tests to make them pass — fix the code instead.
7. **Prefer Odoo CE base modules — don't reinvent them.** This is a Community-Edition project: lean on Odoo's stock, bundled modules as the substrate for features wherever possible. Common reuse targets for a school system include `base` / `contacts` (students, parents/guardians, teachers as `res.partner`), `hr` (teachers and staff as `hr.employee`), `calendar` (class schedules, exam schedules, parent-teacher conferences), `event` / `event_sale` (school events, workshops, field trips with ticketing), `product` (courses, subjects, school supplies as products), `sale` / `account` (tuition billing, invoicing, payment terms), `stock` (books, uniforms, school supply inventory), `mail` (chatter, notifications, activities on student/enrollment/grade records), `portal` + `website` (student/parent self-service — view grades, attendance, invoices), and `survey` (exams, quizzes, feedback forms). In practice this means: (a) when the Blueprint depends on a base module, list it in `__manifest__.py`'s `depends` and inherit/extend existing models (e.g. `_inherit = "res.partner"`) rather than creating parallel ones; (b) if the Blueprint defines a model or field that duplicates functionality Odoo CE already provides, stop and re-consult Gemini via `/ask gemini` before implementing — flag it as a potential reuse opportunity rather than silently coding the duplicate.

**Workflow**
1. Red consults Gemini → receives a Blueprint.
2. Red hands the Blueprint to Claude → Claude executes it per the Execution Rules above.
3. On design-level blockers mid-execution, Claude re-consults Gemini (`/ask gemini`) before proceeding.

## Tech stack & tooling

- **Python**: 3.12 (pinned in `.python-version`, matching Odoo 19's target).
- **Framework**: Odoo 19 Community.
- **Package manager**: `uv` — `uv.lock` is committed, so use `uv sync` rather than `pip install`.
- **Linter/formatter**: `ruff` (configured in `pyproject.toml`, line length 120, `target-version = "py312"`).
- **Pre-commit**: trailing-whitespace, end-of-file-fixer, check-yaml, check-xml, check-added-large-files, ruff, ruff-format.

## Common commands

```bash
# Install dev dependencies into .venv
uv sync

# Run the placeholder entry point
uv run python main.py

# Lint / format directly
uv run ruff check .
uv run ruff format .

# Install pre-commit hooks (once per clone)
uv run pre-commit install

# Run all hooks against all files
uv run pre-commit run --all-files

# Run a specific hook against changed files
uv run pre-commit run ruff --files <path>
uv run pre-commit run ruff-format --files <path>
```

Tests run via Odoo's own test harness, **not** pytest:

```bash
# Run a module's tests (requires a running Odoo database)
odoo-bin -d <db> -i <module> --test-enable --stop-after-init

# Run tests for a specific tag
odoo-bin -d <db> -i <module> --test-enable --test-tags=<tag> --stop-after-init
```

Every module must have a `tests/` directory with `__init__.py` importing the test modules. Test classes inherit `odoo.tests.common.TransactionCase` (for data/model tests) or `odoo.tests.common.HttpCase` (for controller/UI tests). File naming: `test_<feature>.py`.

## Coding standards for Odoo modules

When adding an Odoo addon, follow the standard Odoo 19 layout:

- `models/` — Python business logic; inherit from `models.Model` or `models.TransientModel`.
- `views/` — XML for backend views (form, tree, kanban) and menus.
- `security/` — `ir.model.access.csv` and XML record rules.
- `data/` — XML for default/seed data or sequences (always loaded on install).
- `demo/` — XML for demo data (only loaded when the database has "Demo Data" enabled).
- `__manifest__.py`, `__init__.py`, and `README.md` at the module root.

Conventions:

1. **File naming** — Python files named after the model (`model_name.py`); XML view files named `model_name_views.xml`.
2. **No speculative JavaScript** — don't introduce OWL components or frontend JS unless explicitly asked.
3. **PEP8-compliant, 120-char lines** — pre-commit will catch formatting, but write clean code up front.
4. **Every module must have a `README.md`.** Create one at the module root (sibling of `__manifest__.py`) the moment a new module is scaffolded, and **keep it updated** whenever the module's purpose, models, views, security model, or external dependencies change. This README is committed and ships with the module — it is not optional and is distinct from the "no auto-README in `docs/plan/` or `docs/guide/`" rule below. Minimum sections: module name + one-line purpose, what it provides (models/views/menus added), dependencies, and any setup/configuration steps.
5. **Every module must have a Mermaid ERD.** Each module has a corresponding `docs/guide/<module>-erd.md` file containing a Mermaid `erDiagram` showing its models, fields, and relationships. **Keep it updated** whenever models, fields, or relationships are added, removed, or changed — this includes changes made by later modules that extend the same models. If a change in module B adds fields or relationships to a model defined in module A, update module A's ERD as well.
6. **Every module must have demo data.** Each module must include a `demo/` directory with XML files providing realistic sample records (students, teachers, classes, enrollments, grades, etc.) that showcase the module's features. Demo files are listed under the `demo` key in `__manifest__.py` (not `data`) — they only load when the database has "Demo Data" enabled. **Keep demo data updated** when new features or fields are added. Demo data should be realistic and interconnected across modules (e.g. a demo student should have enrollments, a schedule, attendance records, grades, invoices, etc.) so the system looks "alive" on first install. Use `noupdate="1"` in demo XML. Demo records from upstream modules should be referenced by external ID in downstream modules (e.g. a grading module's demo records reference student demo IDs from the base module).

## Documentation conventions

All Markdown documentation lives under `docs/` and is split into two folders with **opposite commit policies**:

- `docs/plan/` — **Plans / Blueprints. NOT committed.** Whenever Claude or Gemini drafts a plan, blueprint, design sketch, investigation note, or any "what we're about to do" document, write it as a Markdown file under `docs/plan/`. Name the file after the thing being planned, in `kebab-case.md` (e.g. `student-model.md`, `tuition-billing-rules.md`, `migrate-to-postgres-17.md`). This folder is gitignored — plans are working artifacts shared between Red, Claude, and Gemini, not project deliverables.
- `docs/guide/` — **Guides. Committed.** Anything intended for a reader/user (how-to-use, setup guides, module documentation, architecture overviews, runbooks) goes here as `kebab-case.md`. These files **must** be tracked by git and shipped with the repo.

Rules:
1. Never write a plan to the repo root or to `docs/guide/` by mistake — plans belong in `docs/plan/` and stay local.
2. Never put a guide in `docs/plan/` — it would be invisible to anyone who clones the repo.
3. If the right folder does not yet exist, create it (`mkdir -p docs/plan` or `mkdir -p docs/guide`) before writing the file.
4. Do not auto-create README.md / index.md inside these folders unless explicitly asked.

## Git commits

- **Always sign commits with both `-s` and `-S`** (e.g. `git commit -s -S -m "..."`). `-s` adds the `Signed-off-by` trailer; `-S` GPG-signs the commit. This applies to every commit in this repo, no exceptions.
- **Do not add yourself as a co-author.** No `Co-Authored-By: Claude ...` trailer, no "Generated with Claude Code" footer, no attribution of any kind in the commit message. The `Signed-off-by` line from `-s` belongs to Red, not to you.

## Odoo 19 breaking changes (verified against odoo:19.0 Docker image)

These differ from Odoo 17/18 and most online tutorials. Always follow these patterns:

1. **`res.groups` — no `category_id`, use `privilege_id`.**
   Odoo 19 restructured the group hierarchy: `ir.module.category` → `res.groups.privilege` → `res.groups`. Create a `res.groups.privilege` record first, then set `privilege_id` on each `res.groups` record. Never use `category_id` on `res.groups` — it doesn't exist.

2. **`res.groups` — `users` field renamed to `user_ids`.**
   Use `<field name="user_ids" eval="[(4, ref('base.user_admin'))]"/>`, not `users`.

3. **Search views — `expand` attribute removed from `<group>`.**
   Use `<group>` (no attributes) for group-by filters in search views. The old `<group expand="0" string="Group By">` raises a validation error.

4. **`ir.cron` — `numbercall` field removed.**
   CRONs run indefinitely by default. Remove any `<field name="numbercall">` from XML data.

5. **`_sql_constraints` deprecated** (warning, not error).
   Use `model.Constraint` on the model class instead. Existing `_sql_constraints` still work but log a warning.

6. **`res.users` — `groups_id` renamed to `group_ids`.**
   Use `"group_ids": [(6, 0, [group.id])]` in Python and `<field name="group_ids">` in XML, not `groups_id`.

7. **Product types:** `type` field still accepts `service`, `consu`, `product`. Use `type` in XML data (not `detailed_type`).

8. **Portal homepage entries** use a categorized layout in Odoo 19.
   - Entries go inside category divs (`portal_client_category`, `portal_service_category`, etc.), NOT directly inside `o_portal_docs`.
   - Enable a category with `<t t-set="portal_service_category_enable" t-value="True"/>` before `o_portal_docs`.
   - Add entries via `<div id="portal_service_category" position="inside">`.
   - Cards default to `d-none` (hidden) and are revealed by JS counter loading. Use `<t t-set="config_card" t-value="True"/>` to always show a card (like Addresses/Connection & Security).

## Known quirks

- The canonical venv is `.venv/`, which `.gitignore` already covers.
- A legacy `main.py` placeholder exists at the repo root from the initial scaffold. It is not used by any module.
