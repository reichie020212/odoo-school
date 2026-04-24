# `school_comms` — Entity Relationship Diagram

`school_comms` defines no new business models — it ships **data records** only: three `mail.template` records and three `base.automation` rules that wire them to state transitions on upstream school models. Each automation rule also owns an `ir.actions.server` record that the rule invokes.

```mermaid
erDiagram
    MAIL_TEMPLATE_FEE_INVOICE_READY }o--|| SCHOOL_FEE_ENROLLMENT : "model_id"
    MAIL_TEMPLATE_REPORT_CARD_FINAL }o--|| SCHOOL_REPORT_CARD : "model_id"
    MAIL_TEMPLATE_EXAM_PUBLISHED }o--|| SCHOOL_EXAM : "model_id"

    AUTOMATION_FEE_INVOICE_NOTIFY ||--|| MAIL_TEMPLATE_FEE_INVOICE_READY : "server action template_id"
    AUTOMATION_REPORT_CARD_FINAL_NOTIFY ||--|| MAIL_TEMPLATE_REPORT_CARD_FINAL : "server action template_id"
    AUTOMATION_EXAM_PUBLISHED_NOTIFY ||--|| MAIL_TEMPLATE_EXAM_PUBLISHED : "server action template_id"

    AUTOMATION_FEE_INVOICE_NOTIFY }o--|| SCHOOL_FEE_ENROLLMENT : "fires on state→invoiced"
    AUTOMATION_REPORT_CARD_FINAL_NOTIFY }o--|| SCHOOL_REPORT_CARD : "fires on state→final"
    AUTOMATION_EXAM_PUBLISHED_NOTIFY }o--|| SCHOOL_EXAM : "fires on state→published"

    MAIL_TEMPLATE_FEE_INVOICE_READY {
        char name "School: Fee Invoice Ready"
        char subject "{{ object.structure_id.name }}"
        char partner_to "{{ object.student_id.id }}"
        html body_html "inline QWeb with t-out tags"
    }
    MAIL_TEMPLATE_REPORT_CARD_FINAL {
        char name "School: Report Card Finalized"
        char subject "{{ object.name }}"
        char partner_to "{{ object.student_id.id }}"
    }
    MAIL_TEMPLATE_EXAM_PUBLISHED {
        char name "School: Exam Published"
        char subject "{{ object.name }}"
    }

    AUTOMATION_FEE_INVOICE_NOTIFY {
        char trigger "on_create_or_write"
        char filter_pre_domain "[('state','!=','invoiced')]"
        char filter_domain "[('state','=','invoiced')]"
    }
    AUTOMATION_REPORT_CARD_FINAL_NOTIFY {
        char trigger "on_create_or_write"
        char filter_pre_domain "[('state','!=','final')]"
        char filter_domain "[('state','=','final')]"
    }
    AUTOMATION_EXAM_PUBLISHED_NOTIFY {
        char trigger "on_create_or_write"
        char filter_pre_domain "[('state','!=','published')]"
        char filter_domain "[('state','=','published')]"
    }
```

## Notes

- **No new Odoo models** are defined. `school_comms` is purely configuration: three `mail.template` records, three `base.automation` records, and three `ir.actions.server` records that belong to the automations (`usage='base_automation'`, `state='mail_post'`).
- **State-transition semantics** are expressed via the pre/post filter domain pair: the pre-domain matches BEFORE the write, the post-domain matches AFTER — so the rule only fires on the exact transition into the target state.
- **Mail delivery** uses `mail_post_method='comment'` so messages land in the record's chatter, which reaches all followers (including guardians, who are auto-subscribed by upstream modules like `school_fees`).
- **No QWeb CDATA** in the template body — Odoo 19's RelaxNG schema rejects `type="html"` fields with CDATA; templates use inline HTML with `<t t-out>` directives instead.
