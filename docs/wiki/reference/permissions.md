---
title: Permissions matrix
description: Who can do what across the School Management System
published: true
date: 2026-04-25
tags: reference, security, permissions
editor: markdown
---

# Permissions matrix

Access is granted at two levels:

1. **Internal users** (`base.group_user`) — any staff with a backend login. They get read access to school **reference / structural** data automatically so the standard Odoo flows (Contacts, Sales, HR, Purchase) don't break on `res.partner` / `hr.employee` / `product.template` forms that inherit school fields. They do NOT see transactional data (grades, fees, loans, etc.) without further groups.
2. **School Management groups** — three groups bound to the Odoo 19 `res.groups.privilege` *School Management*:
   - **Reader** — read-only on all school models (including transactional).
   - **User** — everyday ops: students, classrooms, courses, attendance, exam results, fee enrollments, scholarships, library loans, canteen transactions, shop sales, transport assignments.
   - **Manager** — everything User can do plus: academic year lifecycle, grading scales, fee structures, library catalog, canteen dietary tags, shop items, automation rules, the admission-number sequence.

Each School group inherits the lower one via `implied_ids` — Manager ⊃ User ⊃ Reader.

> **Install-time note:** `school_base` ships a `post_init_hook` that auto-grants `base.user_admin` the School Manager group so a fresh install has a usable sysadmin on first login. Other users need the group granted through **Settings → Users & Companies → Users**.

## Per-model access

| Model | Internal (`base.group_user`) | School Reader | School User | School Manager |
|---|---|---|---|---|
| `school.academic.year` | R | R | R | RWCU |
| `school.academic.term` | R | R | RWC | RWCU |
| `school.classroom` | R | R | RWC | RWCU |
| `res.partner` (school fields) | via core ACLs | R | RWC | RWCU |
| `hr.employee` (teacher fields) | via core ACLs | R | RW | RWCU |
| `school.subject` | R | R | RWC | RWCU |
| `school.course` + `.schedule.rule` | — | R | RWC | RWCU |
| `school.attendance` | — | R | RWC | RWCU |
| `school.grading.scale` + `.band` | R | R | R | RWCU |
| `school.exam.type` | R | R | R | RWCU |
| `school.exam` | — | R | RWC | RWCU |
| `school.exam.result` | — | R | RWC | RWCU |
| `school.report.card` + `.line` | — | R | RWC | RWCU |
| `school.fee.structure` + `.line` | — | R | R | RWCU |
| `school.fee.enrollment` | — | R | RWC | RWCU |
| `school.scholarship` | — | R | RWC | RWCU |
| `product.template` (`is_school_fee` / `is_canteen_item` / `is_school_shop_item`) | via core ACLs | R | R | RWCU |
| `school.library.book` + `.copy` | — | R | R | RWCU |
| `school.library.loan` | — | R | RWC | RWCU |
| `school.library.category` | R | R | R | RWCU |
| `school.library.author` | R | R | R | RWCU |
| `school.canteen.wallet` | — | R | RWC | RWCU |
| `school.canteen.transaction` | — | R | RWC | RWCU |
| `school.canteen.menu` | — | R | RWC | RWCU |
| `school.canteen.dietary.tag` | R | R | R | RWCU |
| `school.shop.sale` + `.line` | — | R | RWC | RWCU |
| `school.transport.vehicle` | — | R | R | RWCU |
| `school.transport.route` + `.stop` | — | R | R | RWCU |
| `school.transport.assignment` | — | R | RWC | RWCU |

`R` = read, `W` = write, `C` = create, `U` = unlink (delete). `—` means the group has no access on that model. "via core ACLs" means the model uses Odoo's standard access (typically readable by all internal users).

**Why the Internal column matters:** every m2o / m2m field from a school model onto a core model (e.g. `res.partner.student_classroom_id`, `res.partner.canteen_allergy_tag_ids`) forces the ORM to **read** the target on form load, regardless of whether the view hides the field. Reference / catalog data (academic year, classroom, subject, dietary tag, grading scale, exam type, library category/author) therefore has to be readable by any internal user, or opening a non-student partner form would fail with an AccessError. Write access remains gated by School Manager.

## Portal users (students / guardians)

Portal users are in `base.group_portal` **but not** in any `school_*` group. They get a different access path:

| Model | Access for portal users |
|---|---|
| `school.exam` | R (limited by record rule to own/ward exam scope) |
| `school.exam.result` | R (limited to own/ward results) |
| `school.report.card` + `.line` | R (limited to own/ward report cards) |
| `school.fee.enrollment` | R (limited to own/ward enrollments) |
| `school.fee.structure` + `.line` | R (for invoice context) |
| `school.course` / `school.subject` / `school.classroom` / `school.academic.term` / `school.academic.year` | R (catalog read-only) |

All other school models (library, canteen, shop, transport, etc.) are **invisible** to portal users. The portal shows a curated dashboard at `/my/school` — see [portal guide](../portal-guides/01-student-and-guardian-dashboard.md).

## Record rules

On top of the group ACLs, record rules narrow **which rows** a user can see:

| Rule | Applies to | Group | Domain |
|---|---|---|---|
| Report card — portal user owns it | `school.report.card` | `base.group_portal` | `student_id = user.partner` OR in wards |
| Report card line — portal user owns it | `school.report.card.line` | `base.group_portal` | same |
| Exam result — portal user owns it | `school.exam.result` | `base.group_portal` | same |
| Fee enrollment — portal user owns it | `school.fee.enrollment` | `base.group_portal` | same |

Backend School groups (Reader / User / Manager) have NO row-level restrictions — staff see everyone's records.

## Adding a new row-level rule

If you need a teacher to see only their own courses' data (not the whole school), add:

```python
# hypothetical rule; not shipped
@api.model
def _teacher_own_course_domain(self):
    return [('course_id.teacher_id.user_id', '=', self.env.user.id)]
```

Wire it as an `ir.rule` record scoped to the teacher group. See `school_portal/security/school_portal_security.xml` for shipped examples.

## Auditing access

- **Settings → Users & Companies → Users** lists every user and their groups. Filter by group to see membership.
- **Settings → Technical → Security → Record Rules** lists every row-level rule.
- **Settings → Technical → Security → Access Rights** is the full ACL grid.
- A user can check their own rights in developer mode: **My Profile → Preferences → Developer Tools → View security rules**.

## Next steps

- [Odoo 19 specifics we rely on →](odoo-19-specifics.md)
- [Back to reference index →](../reference/)
