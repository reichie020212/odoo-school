---
title: Odoo 19 specifics you need to know
description: Breaking changes from Odoo 17/18 that the School Management System relies on
published: true
date: 2026-04-25
tags: reference, odoo-19, upgrade
editor: markdown
---

# Odoo 19 specifics you need to know

These patterns differ from Odoo 17/18 and most online tutorials. The School Management System relies on them throughout.

## 1. `res.groups` — no `category_id`, use `privilege_id`

Odoo 19 restructured the group hierarchy:

```
ir.module.category  →  res.groups.privilege  →  res.groups
```

Creating a group:

```xml
<record id="privilege_school_management" model="res.groups.privilege">
    <field name="name">School Management</field>
    <field name="sequence">10</field>
</record>

<record id="group_school_reader" model="res.groups">
    <field name="name">Reader</field>
    <field name="privilege_id" ref="privilege_school_management"/>
</record>
```

**Never** use `category_id` on `res.groups` — the field doesn't exist in Odoo 19.

## 2. `res.groups.users` renamed to `user_ids`

```xml
<field name="user_ids" eval="[(4, ref('base.user_admin'))]"/>
```

Not `users`.

## 3. `res.users.groups_id` renamed to `group_ids`

```python
admin.write({'group_ids': [(4, manager_group.id)]})
```

Not `groups_id`. XML views use `<field name="group_ids">` too.

## 4. Search views — `expand` attribute removed from `<group>`

Old (Odoo 17/18):

```xml
<search>
    ...
    <group expand="0" string="Group By">
        <filter name="group_state" string="Status" context="{'group_by': 'state'}"/>
    </group>
</search>
```

New (Odoo 19):

```xml
<search>
    ...
    <group>
        <filter name="group_state" string="Status" context="{'group_by': 'state'}"/>
    </group>
</search>
```

The old form raises a validation error on load.

## 5. `ir.cron` — `numbercall` field removed

CRONs run indefinitely by default. Remove any `<field name="numbercall">` from data XML.

## 6. `_sql_constraints` deprecated

Old:

```python
class MyModel(models.Model):
    _name = 'my.model'
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Name must be unique.'),
    ]
```

New:

```python
class MyModel(models.Model):
    _name = 'my.model'

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Name must be unique.',
    )
```

The old pattern still works but logs a warning. All 11 school modules use `models.Constraint`.

## 7. Product `type` field

Still accepts `service`, `consu`, `product`. Use `type` in XML data, **not** `detailed_type` (which was used in Odoo 15/16 during the transition).

## 8. `<list>` vs `<tree>`

Odoo 19 prefers `<list>` for list views:

```xml
<record id="view_xxx_list" model="ir.ui.view">
    <field name="arch" type="xml">
        <list>
            <field name="name"/>
        </list>
    </field>
</record>
```

`<tree>` still works for backward compat but the new idiom is `<list>`. All 11 school modules use `<list>`.

## 9. Stored computed fields with `required=True` need `precompute=True`

If a field is `compute + store + required`, Odoo 17+ runs the NOT-NULL check BEFORE the compute runs — so you get a `NotNullViolation` on INSERT.

Fix:

```python
name = fields.Char(
    compute="_compute_name",
    store=True,
    readonly=False,
    required=True,
    precompute=True,          # ← this forces the compute BEFORE the INSERT
)
```

This bit us once during the school_academics build (see commit `59e7b98`). Applied consistently thereafter.

## 10. `<field type="html">` with CDATA breaks RelaxNG

Mail templates in Odoo 19's stricter RelaxNG schema **reject**:

```xml
<field name="body_html" type="html"><![CDATA[<p>hi</p>]]></field>
```

Use inline HTML (no CDATA):

```xml
<field name="body_html" type="html">
    <div>
        <p>hi</p>
    </div>
</field>
```

Inside the inline HTML you can still use `<t t-out="...">` for substitution. Hit this in `school_comms` during build.

## 11. Portal homepage categorised layout

Odoo 19 portal home uses category divs, not direct entries in `o_portal_docs`:

```xml
<template id="portal_my_home_school" name="Portal My Home : School"
          inherit_id="portal.portal_my_home">
    <xpath expr="//div[hasclass('o_portal_docs')]" position="before">
        <t t-set="portal_client_category_enable" t-value="True"/>
    </xpath>
    <div id="portal_client_category" position="inside">
        <t t-call="portal.portal_docs_entry">
            <t t-set="title">School</t>
            <t t-set="url" t-value="'/my/school'"/>
            <t t-set="config_card" t-value="True"/>
        </t>
    </div>
</template>
```

Cards default to `d-none` and are revealed by JS-loaded counters. `config_card=True` makes the card always visible (used for fixed entries like ours).

## 12. `base.automation` and `on_state_set`

Tempting to use:

```xml
<field name="trigger">on_state_set</field>
<field name="trg_selection_field_id" ref="..."/>
```

But `trg_selection_field_id` targets **one option row** (`ir.model.fields.selection`), not the whole selection field. For simple "fire when state transitions to X" rules, it's easier to use:

```xml
<field name="trigger">on_create_or_write</field>
<field name="filter_pre_domain">[('state', '!=', 'invoiced')]</field>
<field name="filter_domain">[('state', '=', 'invoiced')]</field>
```

This matches the pre-update state + post-update state and only fires on the exact transition. `school_comms` uses this pattern for all three rules.

## 13. `account.move` partial unique index tips

Use PostgreSQL EXCLUDE for partial uniqueness:

```python
_assignment_unique_active = models.Constraint(
    "EXCLUDE USING btree (student_id WITH =, academic_year_id WITH =) WHERE (state = 'active')",
    "Student already has an active assignment for this academic year.",
)
```

Used on `school.transport.assignment` — students can have many historical records, only one active.

## Next steps

- [Architecture overview →](architecture.md)
- [Permissions matrix →](permissions.md)
