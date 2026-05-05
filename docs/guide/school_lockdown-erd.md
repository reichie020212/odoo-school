# `school_lockdown` — Entity Relationship Diagram

`school_lockdown` is a **behaviour-only** module: it defines no new models, no new fields on existing models, and no new relations. There is therefore nothing to draw in an ER diagram.

For completeness, here is what the module *touches*:

```mermaid
flowchart LR
    subgraph base[Odoo base]
        RES_USERS[res.users]
        ICP[ir.config_parameter]
    end

    subgraph lockdown[school_lockdown]
        OVERRIDE_PCP["override<br/>preference_change_password"]
        VIEW_OVERRIDE["XML inherit<br/>view_users_form_simple_modif"]
        DATA_RECORD["data record<br/>auth_signup.reset_password = False"]
    end

    OVERRIDE_PCP -.inherits.-> RES_USERS
    VIEW_OVERRIDE -.inherits.-> RES_USERS
    DATA_RECORD -.writes.-> ICP
```

If a future change adds models or fields to this module, replace the flowchart above with a real `erDiagram` block matching the convention used by the other `docs/guide/<module>-erd.md` files.
