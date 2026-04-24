# School Exams

**Odoo 19 Community module — assessment, grading, and report cards for the School Management System.**

Depends on `school_academics` (for courses) and `school_base` (for students + security groups).

## Purpose

Covers the full assessment lifecycle:

- Configurable grading scales (US A–F, Philippine DepEd, or a school's own).
- Exam types with default weights (Quiz / Midterm / Final / …).
- Exams tied to a course, with per-exam weight, max score, and an optional scale override.
- Student exam results with computed percentage, letter grade, and GPA value.
- Term report cards with weighted course grades, overall GPA, and a printable QWeb PDF.

## What this module provides

### Models

| Model | Summary |
|---|---|
| `school.grading.scale` | Grading scale (exactly one marked default, used when exams don't specify). |
| `school.grading.scale.band` | Letter / minimum % / GPA row within a scale. |
| `school.exam.type` | Kind of assessment with default weight. |
| `school.exam` | Concrete exam instance: course × type × date × max_score × weight + optional scale override. |
| `school.exam.result` | Per-student score with computed percentage, letter, and GPA. Unique per (exam, student). |
| `school.report.card` | Per-student, per-term snapshot with weighted course lines and overall GPA. Unique per (student, term). |
| `school.report.card.line` | Per-course row with weighted %, letter, GPA, and an editable teacher remark. |

### Weighted course grade

For each course line on a report card:

```
graded_results = student's results on course exams whose state ∈ {published, closed} and weight > 0
if graded_results is empty → line is "Incomplete", no penalty
else:
    percentage = Σ(result.percentage × exam.weight) / Σ(exam.weight)
    letter_grade = contributing exam's effective scale → lookup(percentage)
    gpa_value   = corresponding band's GPA
```

The overall card is the straight mean of line percentages (excluding incomplete lines) and line GPAs.

### Report card PDF

- QWeb template: `school_exams.report_school_report_card`.
- Action: `school_exams.action_report_school_report_card` (bound as a "Print → Report Card" entry on the record).
- Layout: school header (`res.company`), student info + admission #, term, academic year, course table (subject | teacher | % | letter | GPA | remark), overall footer, signature lines.

### Menus

- **School → Academics → Exams / Exam Results / Report Cards**.
- **School → Configuration → Exam Types / Grading Scales** (manager-only).

### Security

Uses `school_base` groups:

- **Reader** — read-only on all exam records.
- **User** — create/read/write exams, results, report cards; read-only on exam types and scales (managed by admins).
- **Manager** — full CRUD including scales and types, archive/state transitions.

## Dependencies

- `school_academics`
- `school_base`
- `mail`

## Installation

```bash
odoo-bin -d school_dev -i school_exams
```

Installing pulls in `school_academics` + `school_base` + their deps.

## Demo data

Loaded when "Demo Data" is enabled:

- 2 grading scales — `scale_us` (default, A/B/C/D/F, 4.0 GPA) and `scale_deped_ph` (Philippine DepEd 1.00–5.00).
- 3 exam types — Quiz (20%), Midterm (30%), Final (50%).
- 2 published exams on `course_math_9a` — a 50-point quiz and a 100-point midterm.
- 4 results — Alice (90% quiz, 87% midterm → 88.2% B) and Ethan (80% quiz, 72% midterm → 75.2% C).
- 1 draft report card for Alice covering S1 2026-2027 with a single Math course line and a teacher remark.

## Tests

```bash
odoo-bin -d school_dev -i school_exams --test-enable --test-tags=/school_exams --stop-after-init
```

Covers scale band lookup, single-default enforcement, exam uniqueness, exam name autocompute, weight seeding, state transitions, placeholder generation, result uniqueness + enrollment + score-range checks, report-card weighted formula, incomplete handling, and card state lifecycle.
