# School Base

**Odoo 19 Community module — foundation for the School Management System.**

## Purpose

Provides the shared records every downstream school module depends on: academic years, terms, classrooms, students, guardians, and teachers. No domain logic for courses, exams, fees, library, etc. — those live in follow-up modules that `depend` on this one.

## What this module provides

### Models

| Model | Summary |
|---|---|
| `school.academic.year` | Yearly session with draft/active/archived lifecycle. Only one year can be active at a time. |
| `school.academic.term` | Terms within an academic year; dates must fall inside the year and cannot overlap other terms. |
| `school.classroom` | Graded classroom (K–12), with optional homeroom teacher, capacity enforcement, and live `student_count`. |
| `res.partner` (extended) | `is_student` / `is_guardian` flags, student profile fields (admission #, DOB, gender, status, medical, emergency contact), symmetric guardian ↔ ward m2m. |
| `hr.employee` (extended) | `is_teacher` flag, school employee number, qualifications, homeroom classrooms one2many, school hire date. |

### Views & menus

- Top-level **School** menu → Students, Guardians, Teachers, Classrooms, Configuration (Academic Years, Terms, Admission Number Sequence).
- Inherited partner form adds a "Student Information" page (shown when `is_student`), "Guardians" page (when `is_student`), and "Wards" page (when `is_guardian`).
- Inherited employee form adds a "Teaching" page with teacher fields and a list of homeroom classrooms.

### Security

Three groups bound to the **School Management** privilege (Odoo 19's `res.groups.privilege`):

- **Reader** — read-only on all school records.
- **User** — day-to-day ops on students, classrooms, terms (read/write/create).
- **Manager** — full CRUD including academic year lifecycle; has access to the Configuration menu.

ACLs are in `security/ir.model.access.csv`; record rules are deferred to later modules.

### Demo data

Loaded when "Demo Data" is enabled on the database:

- 1 academic year (2026–2027) with 2 terms.
- 4 classrooms (9A, 9B, 10A, 10B) with homeroom teachers.
- 4 teachers (Maria Santos, Juan Dela Cruz, Anna Reyes, Pedro Mendoza).
- 4 families × 2 guardians × 2 students = 8 guardians and 8 students, all linked.
- 2 non-admin internal users for testers and viewers:

  | Login | Password | Group | Purpose |
  |---|---|---|---|
  | `school_user` | `school_user` | School User (+ Reader) | Day-to-day operations — for testers exercising create/edit flows. |
  | `school_reader` | `school_reader` | School Reader | Read-only — for viewers reviewing the data without changing anything. |

  Demo passwords are intentionally trivial; never enable demo data in production.

External IDs follow the pattern `school_base.<record_id>` (e.g. `school_base.student_alice_garcia`) so downstream modules can reference them.

## Dependencies

- `base`
- `contacts`
- `hr`
- `mail`

## Installation

This module is installed like any other Odoo addon. Inside the project's Docker environment the repo is mounted at `/mnt/extra-addons/odoo-school`:

```bash
odoo-bin -d school_dev -i school_base
```

To load with demo data enabled, make sure the database was created with the "Demo Data" option and pass `--without-demo=False` if needed, or tick the option during Initialise Database.

## Configuration

### Admission number format

Admission numbers are auto-generated from an `ir.sequence` record (`school.student.admission`). The default prefix is `%(range_year)s-` with padding 5, producing values like `2026-00001`.

To change the format, go to **School → Configuration → Admission Number Sequence** (manager access required) and edit the sequence's prefix, padding, or next-number fields from the UI.

### Security

Assign users to the appropriate group (Reader / User / Manager) from **Settings → Users & Companies → Users**.

## Tests

```bash
odoo-bin -d school_dev -i school_base --test-enable --stop-after-init
```

Covers:

- Academic year lifecycle (single-active constraint, date range, uniqueness).
- Term constraints (within year, no overlap, per-year unique code).
- Classroom constraints (per-year unique code, capacity, homeroom must be a teacher).
- Student creation (auto admission number, uniqueness, DOB-in-past, guardian symmetry, cannot be own guardian, promotion flow).
- Teacher creation (uniqueness, non-teachers excluded from teacher queries).
