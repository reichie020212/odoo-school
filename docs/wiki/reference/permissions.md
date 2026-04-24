---
title: Permissions matrix
description: Who can do what across the School Management System
published: true
date: 2026-04-25
tags: reference, security, permissions
editor: markdown
---

# Permissions matrix

All access runs through three groups bound to the **School Management** privilege (Odoo 19 `res.groups.privilege`):

- **Reader** — read-only on all school models.
- **User** — everyday ops: students, classrooms, courses, attendance, exam results, fee enrollments, scholarships, library loans, canteen transactions, shop sales, transport assignments.
- **Manager** — everything User can do plus: academic year lifecycle, grading scales, fee structures, library catalog, canteen dietary tags, shop items, automation rules, the admission-number sequence.

Each group inherits the lower one via `implied_ids` — Manager is a superset of User is a superset of Reader.

## Per-model access

| Model | Reader | User | Manager |
|---|---|---|---|
| `school.academic.year` | R | R | RWCU |
| `school.academic.term` | R | RWC | RWCU |
| `school.classroom` | R | RWC | RWCU |
| `res.partner` (school fields) | R | RWC | RWCU |
| `hr.employee` (teacher fields) | R | RW | RWCU |
| `school.subject` | R | RWC | RWCU |
| `school.course` + `.schedule.rule` | R | RWC | RWCU |
| `school.attendance` | R | RWC | RWCU |
| `school.grading.scale` + `.band` | R | R | RWCU |
| `school.exam.type` | R | R | RWCU |
| `school.exam` | R | RWC | RWCU |
| `school.exam.result` | R | RWC | RWCU |
| `school.report.card` + `.line` | R | RWC | RWCU |
| `school.fee.structure` + `.line` | R | R | RWCU |
| `school.fee.enrollment` | R | RWC | RWCU |
| `school.scholarship` | R | RWC | RWCU |
| `product.template` (`is_school_fee` / `is_canteen_item` / `is_school_shop_item`) | R | R | RWCU |
| `school.library.book` + `.copy` | R | R | RWCU |
| `school.library.loan` | R | RWC | RWCU |
| `school.library.category` + `.author` | R | R | RWCU |
| `school.canteen.wallet` | R | RWC | RWCU |
| `school.canteen.transaction` | R | RWC | RWCU |
| `school.canteen.menu` | R | RWC | RWCU |
| `school.canteen.dietary.tag` | R | R | RWCU |
| `school.shop.sale` + `.line` | R | RWC | RWCU |
| `school.transport.vehicle` | R | R | RWCU |
| `school.transport.route` + `.stop` | R | R | RWCU |
| `school.transport.assignment` | R | RWC | RWCU |

`R` = read, `W` = write, `C` = create, `U` = unlink (delete).

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
