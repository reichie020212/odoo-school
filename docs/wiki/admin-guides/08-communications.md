---
title: Communications — mail templates and automation
description: Automated emails for fee invoices, report cards, and published exams
published: true
date: 2026-04-25
tags: admin, mail, automation, notifications
editor: markdown
---

# Communications — mail templates and automation

`school_comms` ships three mail templates and three `base.automation` rules that wire state transitions on upstream records to automated chatter messages (which email followers).

## What's shipped

| Template | Fires when | Sends to |
|---|---|---|
| **Fee Invoice Ready** | `school.fee.enrollment.state` transitions to `invoiced` | The student (+ guardians, who are auto-subscribed as invoice followers by `school_fees`) |
| **Report Card Finalized** | `school.report.card.state` transitions to `final` | The student |
| **Exam Published** | `school.exam.state` transitions to `published` | Enrolled students of the course |

The automation rules use the `on_create_or_write` trigger with a `filter_pre_domain` / `filter_domain` pair, so they only fire on the **exact transition** into the target state (not on every save once the record is already in that state).

## Editing a template

**Settings → Technical → Email → Email Templates**. Find the template by name (they all start with `School:`).

The template body uses inline Odoo QWeb with `t-out` directives for value substitution:

```html
<div>
    <p>Dear <t t-out="object.student_id.display_name or ''"/> family,</p>
    <p>
        A new fee invoice has been generated for
        <strong t-out="object.structure_id.name or ''"/>
        (<t t-out="object.term_id.name or ''"/>).
    </p>
    ...
</div>
```

`object` refers to the record the template is being rendered against (e.g. `school.fee.enrollment`). Any field on that model is accessible — including relational traversals like `object.student_id.student_admission_number`.

The subject line uses **Jinja2-style** templating (`{{ ... }}`):

```
Fee invoice ready — {{ object.structure_id.name }}
```

The recipients field (`partner_to`) is also Jinja2:

```
{{ object.student_id.id }}
```

## Editing an automation rule

**Settings → Technical → Automation Rules**. Find the rule by name (they all start with `School:`).

| Field | Meaning |
|---|---|
| **Model** | The record type the rule watches. |
| **Trigger** | `on_create_or_write` for our rules. |
| **Filter Before Update Domain** | Must match the record's state **before** the change. |
| **Filter Domain** | Must match the record's state **after** the change. Both must match for the action to fire. |
| **Actions to Do** | The linked `ir.actions.server` that posts the mail template. |

To disable a rule temporarily, untick **Active**. To delete it, use the Actions menu — the linked action server record is cascade-deleted.

## Adding a new automated mail

Say you want an email when a library loan becomes overdue. Four steps:

1. **Create the template** at Settings → Technical → Email → Email Templates. Model = `school.library.loan`. Write subject + body using `t-out` / `{{ }}`.
2. **Create the automation rule** at Settings → Technical → Automation Rules. Model = `school.library.loan`. Trigger = `on_create_or_write`. Set the pre/post filter domain to match the transition:
   - `filter_pre_domain = [('is_overdue', '=', False)]`
   - `filter_domain = [('is_overdue', '=', True)]`
3. **Add an action** to the rule: type = **Send Email**, template = the one you created, method = `comment` (so it posts to chatter and reaches followers).
4. **Test** by manually forcing a transition on a test record.

If the new rule should ship with the module, dump the records to XML and add a migration file. (Out of scope for this wiki — see `school_comms/data/` for examples.)

## Testing that an email actually fires

1. **Ensure outgoing email is configured**: Settings → Technical → Outgoing Mail Servers. On a dev box you can point this at Mailhog or a free tier of SendGrid.
2. Open a record and trigger the state change (e.g. click **Generate Invoice** on a fee enrollment).
3. Check **Settings → Technical → Email → Emails** — the outgoing message should appear with state `sent` (or `outgoing` while the queue drains).
4. Look at the record's chatter — you should see the mail entry there too.

## Turning all school emails off temporarily

Either:

- Disable the three shipped automation rules (Settings → Technical → Automation Rules → untick Active for each), **or**
- Remove the outgoing mail server config so emails queue but never ship.

## Next steps

- [Operations: backup and restore →](../operations/01-backup-and-restore.md)
- [Portal dashboard walkthrough →](../portal-guides/01-student-and-guardian-dashboard.md)
