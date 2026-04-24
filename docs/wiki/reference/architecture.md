---
title: System architecture
description: Module dependency graph, data flow, and key Odoo 19 idioms used across the suite
published: true
date: 2026-04-25
tags: reference, architecture
editor: markdown
---

# System architecture

## Module dependency graph

```
                               school_homepage
                                      │
                  ┌───────────────────┼────────────────────┐
                  │                   │                    │
            school_portal       school_comms        school_transport
                  │                   │                    │
     ┌────────────┼───────────────────┼────────────────────┤
     │            │                   │                    │
school_academics  │             school_exams         school_library
     │            │                   │                    │
     │            │                   │              school_canteen
     │            │                   │                    │
     │            └───────────────────┴────────────────────┤
     │                                                     │
     │                                               school_shop
     │                                                     │
     │                                                school_fees
     │                                                     │
     └─────────────────────────────────────────────────────┤
                                                           │
                                                      school_base
                                                           │
          Odoo CE: base / contacts / hr / calendar / account / product / stock / mail / base_automation / portal / website
```

Installing **`school_homepage`** pulls in every module transitively. To install a narrower subset, pick the top-most module you need and Odoo resolves the rest.

## Where each piece of data lives

| Concept | Table | Defined in |
|---|---|---|
| Student / guardian partner | `res.partner` with `is_student` / `is_guardian` | `school_base` |
| Teacher employee | `hr.employee` with `is_teacher` | `school_base` |
| Academic year, term, classroom | `school.academic.year` / `school.academic.term` / `school.classroom` | `school_base` |
| Subject, course, schedule rule | `school.subject` / `school.course` / `school.course.schedule.rule` | `school_academics` |
| Session | `calendar.event` (inherited, with `school_course_id`) | `school_academics` |
| Attendance | `school.attendance` | `school_academics` |
| Grading scale, exam, result, report card | `school.grading.scale` / `school.exam` / `school.exam.result` / `school.report.card` / `school.report.card.line` | `school_exams` |
| Fee item | `product.template` with `is_school_fee` | `school_fees` |
| Fee structure, line, enrollment, scholarship | `school.fee.structure` / `.line` / `.enrollment` / `school.scholarship` | `school_fees` |
| Invoice | `account.move` (extended with `school_enrollment_ids`) | `school_fees` |
| Library book, copy, loan | `school.library.book` / `.copy` / `.loan` | `school_library` |
| Canteen wallet, transaction, menu, dietary tag | `school.canteen.wallet` / `.transaction` / `.menu` / `.dietary.tag` | `school_canteen` |
| Shop sale | `school.shop.sale` / `.line` (creates `stock.picking` on confirm) | `school_shop` |
| Transport vehicle, route, stop, assignment | `school.transport.vehicle` / `.route` / `.stop` / `.assignment` | `school_transport` |
| Mail templates + automation rules | `mail.template` / `base.automation` records | `school_comms` |

## Patterns used across the suite

### Flag-on-base-model for specialisation

Students and teachers don't get parallel models. Instead:

- `res.partner` + `is_student` boolean + student-specific fields (`student_admission_number`, `student_classroom_id`, ...).
- `hr.employee` + `is_teacher` boolean + teaching-specific fields.
- `product.template` + `is_school_fee` / `is_canteen_item` / `is_school_shop_item`.

This is the idiomatic Odoo pattern (compare `customer_rank` / `supplier_rank` on `res.partner`). Benefits: students work with Odoo's portal, mail, invoicing out of the box; products work with Odoo's pricing, stock, accounting out of the box.

### `precompute=True` on stored computed required fields

Odoo 17+ changed when stored computes run. Any field with `compute + store + required` needs `precompute=True` or it will fire a `NotNullViolation` on INSERT. Applied consistently across the suite for auto-generated names (`school.course.name`, `school.exam.name`, `school.fee.enrollment.name`, etc.).

### Odoo 19 security: `res.groups.privilege`

Replaced `ir.module.category` on groups. Pattern:

```xml
<record id="privilege_school_management" model="res.groups.privilege">
    <field name="name">School Management</field>
</record>

<record id="group_school_reader" model="res.groups">
    <field name="name">Reader</field>
    <field name="privilege_id" ref="privilege_school_management"/>
</record>
```

All 11 modules route their ACLs through the three groups under this one privilege.

### SQL EXCLUDE for partial uniqueness

`school.transport.assignment` uses a PostgreSQL `EXCLUDE` constraint to enforce "at most one **active** assignment per `(student, academic_year)`":

```python
_assignment_student_year_active_unique = models.Constraint(
    "EXCLUDE USING btree (student_id WITH =, academic_year_id WITH =) WHERE (state = 'active')",
    ...
)
```

Students can have any number of historical `draft` / `ended` assignments but only one currently-active.

### Record rules for portal scoping

Portal users see only their own records via rules like:

```xml
<field name="domain_force">
    ['|',
        ('student_id', '=', user.partner_id.id),
        ('student_id', 'in', user.partner_id.student_ward_ids.ids)]
</field>
```

Applied to `school.exam.result`, `school.report.card`, `school.report.card.line`, `school.fee.enrollment`.

## Further reading

- [Odoo 19 specifics →](odoo-19-specifics.md)
- [Permissions matrix →](permissions.md)
- Per-module ERDs under `docs/guide/<module>-erd.md`.
