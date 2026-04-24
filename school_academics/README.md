# School Academics

**Odoo 19 Community module — curriculum, courses, sessions, and attendance for the School Management System.**

Builds on `school_base`. Reuses Odoo's `calendar` for session scheduling so the academic timetable shows up in the standard calendar views (day/week/month, iCal export, reminders) for every user.

## Purpose

Once `school_base` defines *who* is in the school (students, teachers, classrooms, academic years), `school_academics` defines *what* they do during the term:

- The curriculum catalog (`school.subject`).
- Concrete offerings of those subjects as `school.course` records — one per subject / classroom / term combination, taught by one teacher, with auto-enrolled students.
- A weekly meeting pattern per course that generates `calendar.event` sessions across the term.
- Per-session student attendance with present / absent / late / excused states.

## What this module provides

### Models

| Model | Summary |
|---|---|
| `school.subject` | Curriculum catalog entry (name, code, description, default weekly hours). |
| `school.course` | Offering of a subject — subject × term × classroom × teacher + enrolled students + schedule rules. |
| `school.course.schedule.rule` | Weekly meeting slot (weekday + start time + duration + optional location). |
| `calendar.event` (extended) | Adds `school_course_id`, `school_session_state`, and `school_attendance_ids`; "Mark all present" / "Cancel session" actions. |
| `school.attendance` | Per-student, per-session record with four states (present / absent / late / excused). |

### Enrollment — auto-sync from the classroom roster

Creating a course auto-enrolls every student currently in the classroom. You can still add or remove students explicitly, and there's a **Re-sync Roster** button on the course that reseeds enrollment from the classroom's current students (useful when students are moved between classrooms mid-term).

### Sessions — materialised from a weekly pattern

Each course has a list of weekly schedule rules (e.g. "Monday 08:00 for 1h", "Wednesday 08:00 for 1h"). Pressing **Generate Sessions** on the course walks the term's date range and creates a `calendar.event` for every matching weekday, skipping any sessions that already exist. Repeated presses are safe — only new slots get added.

Sessions are regular `calendar.event` records, so they appear automatically in the calendar module, respect reminders, and can be exported as iCal.

### Attendance — per session, with "Mark All Present"

On any session linked to a course, managers/teachers can press **Mark All Present** to one-click attendance for the whole roster. Individual rows can then be flipped to late / absent / excused as needed.

Attendance enforces two rules:

1. A student can only have one attendance record per session.
2. A student must be enrolled in the course to be marked for one of its sessions.

### Menus

Under the existing **School** root (from `school_base`):

- **School → Academics → Courses** — manage courses (kanban grouped by state).
- **School → Academics → Sessions** — calendar/list view filtered to school sessions only.
- **School → Academics → Attendance** — flat list of attendance records with rich filters.
- **School → Configuration → Subjects** — manage the curriculum catalog (manager-only).

### Security

Uses the three `school_base` groups:

- **Reader** — read-only on all academic records.
- **User** — read/write/create on subjects, courses, sessions (via calendar), and attendance.
- **Manager** — full CRUD including course archive / state transitions.

## Dependencies

- `school_base`
- `calendar`

## Installation

```bash
odoo-bin -d school_dev -i school_academics
```

Installing `school_academics` automatically pulls in `school_base` (which in turn pulls in `base`, `contacts`, `hr`, `mail`).

## Demo data

Loaded when "Demo Data" is enabled:

- 4 subjects — Mathematics, Science, English, History.
- 16 courses — one per subject per classroom (9A, 9B, 10A, 10B from `school_base`) in the first semester of AY 2026-2027, each with a Mon/Wed or Tue/Thu weekly schedule.
- 1 materialised session (`session_math_9a_week1`, Monday 2026-08-03 08:00) with 2 attendance rows (Alice present, Ethan late) — enough to show the attendance UI on first install.

All demo records use external IDs prefixed `school_academics.`. Downstream modules can reference them (e.g. `school_academics.course_math_9a`).

## Tests

```bash
odoo-bin -d school_dev -i school_academics --test-enable --test-tags=/school_academics --stop-after-init
```

Covers:

- **Subject** — CRUD, unique code, archive flag.
- **Course** — auto-enrollment from classroom roster, explicit enrollment, re-sync, unique per (subject, classroom, term), auto-computed name, state transitions.
- **Session materialisation** — expected occurrences from a weekly pattern, idempotent re-runs, no-schedule guard, correct per-rule duration.
- **Attendance** — uniqueness, enrollment enforcement, non-school events rejected, "Mark All Present" adds missing rows and flips state, doesn't overwrite existing rows.
