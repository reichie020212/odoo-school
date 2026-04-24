# School Communications

**Odoo 19 Community module — mail templates and automation rules for school events.**

Depends on `mail`, `base_automation`, `school_base`, `school_academics`, `school_exams`, `school_fees`.

## What it ships

### Mail templates

| XML ID | Model | Trigger |
|---|---|---|
| `mail_template_fee_invoice_ready` | `school.fee.enrollment` | Sent when the enrollment is invoiced. |
| `mail_template_report_card_final` | `school.report.card` | Sent when the report card is finalized. |
| `mail_template_exam_published` | `school.exam` | Sent when the exam is published. |

Each template auto-selects recipients: the student record + their guardians (via `student_guardian_ids`), or all enrolled students (for exam notifications).

### Automation rules

Three `base.automation` records fire on the state change and post the matching template as a chatter message (which emails followers):

- **School: Notify when fee enrollment becomes invoiced**
- **School: Notify when report card is finalized**
- **School: Notify when exam is published**

Admins can disable or tweak these from **Settings → Technical → Automation Rules**.

## Customizing

Duplicate the shipped template, edit wording / styling, and either (a) swap the automation rule's template_id or (b) call `template.send_mail(record.id)` manually.

## Tests

```bash
odoo-bin -d school_dev -i school_comms --test-enable --test-tags=/school_comms --stop-after-init
```

Covers: templates installed, automation rules installed, template body renders against the demo fee enrollment with the student name and structure name in the output.
