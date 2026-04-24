# School Portal

**Odoo 19 Community module — `/my/school` dashboard for students and guardians.**

Depends on `portal`, `school_base`, `school_academics`, `school_exams`, `school_fees`.

## What it does

- Adds a "School" card to Odoo's portal home (`/my`).
- Adds a dedicated `/my/school` dashboard showing:
  - The authenticated user's student(s) — either their own record (student user) or their wards (guardian user).
  - Outstanding fees across all their enrollments.
  - Latest 10 report cards with overall percentage / letter / GPA.
  - Most recent 15 exam results.
  - Latest 10 fee enrollments with amounts.
- Ships record rules so portal users only see records tied to their own partner or their wards.

## Security model

- Adds `base.group_portal` read access to `school.exam.result`, `school.report.card`, `school.report.card.line`, `school.fee.enrollment` (plus supporting catalog models like `school.exam`, `school.course`, `school.classroom`, `school.academic.term/year`, `school.subject`, `school.fee.structure/line`).
- Record rules narrow visibility to records where `student_id == user.partner_id` OR `student_id in user.partner_id.student_ward_ids`.
- Backend school users and managers are unaffected; they retain the ACLs from each upstream module.

## Routes

- `GET /my/school` — dashboard page. Renders `school_portal.portal_my_school`. Auth: `user`.

## Tests

```bash
odoo-bin -d school_dev -i school_portal --test-enable --test-tags=/school_portal --stop-after-init
```

Covers anonymous redirect and authenticated 200 on `/my/school`.
