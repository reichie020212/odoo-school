# School Lockdown

**Odoo 19 Community module — disables self-service password changes and the public reset-password link.**

## Purpose

By default, Odoo lets every authenticated user change their own password via *My Preferences > Account Security > Change Password*, and shows a *Reset Password* link on the login page. For a school deployment that wants password resets to flow through a registrar / sysadmin, both routes need to be closed.

This module is policy-only — it adds no domain models or menus. It only modifies behaviour of `res.users` and `ir.config_parameter`.

## What this module provides

- **View override** of `base.view_users_form_simple_modif`: the *Change Password* section on My Preferences is wrapped with `groups="base.group_system"`, so non-admins simply do not see the button.
- **Python override** of `res.users.preference_change_password`: server-side backstop that raises `UserError` for non-admins, so a crafted RPC cannot bypass the hidden UI.
- **Data record** that sets `ir.config_parameter` `auth_signup.reset_password` to `False`. The `auth_signup` module reads this as the string `'True'` to enable the *Reset Password* link, so any other value disables it.

## What this module deliberately does *not* change

- *Settings > Users > Action: Change Password* (the admin recovery path) is untouched. Admins can still set passwords for any user — that is the recovery mechanism this module assumes.
- Admins changing their own password via My Preferences continues to work; the lockdown only targets users without `base.group_system`.
- The `change.password.own` and `change.password.wizard` transient models are not modified — only the entry points are gated.

## Dependencies

- `base` — for `res.users`, `ir.config_parameter`, and the simple-modif view.
- `auth_signup` — load-order dependency. `auth_signup`'s own data file calls `set_param('auth_signup.reset_password', 'True')` via a `<function>` tag on every install *and every upgrade*. To make `'False'` stick we re-run the same call ourselves and rely on the depends graph to order us after `auth_signup`, so our value is the last write each time.

## Install

```bash
docker compose exec odoo odoo -d school_dev -i school_lockdown --stop-after-init
```

## Uninstall

Removing the module restores the *Change Password* button on My Preferences and removes the Python backstop. The `auth_signup.reset_password` parameter row stays at `False` (because of `noupdate="1"`); flip it back via *Settings > Users & Companies > Settings* if you want the *Reset Password* link to reappear.

## Tests

```bash
docker compose run --rm --no-deps odoo odoo \
    -d test_db -i school_lockdown --test-enable \
    --test-tags=/school_lockdown --stop-after-init
```

Covers: ICP value after install, non-admin blocked from `preference_change_password`, admin still wired to the wizard, and admin-issued password reset (`_change_password`) still succeeds end-to-end via `authenticate`.

## Demo data

Intentionally none — this is a behaviour-only module with no records to seed. The lockdown's effect is observable on a fresh install by logging in as any non-admin demo user (e.g. `demo_user`, `demo_teacher`, `demo_registrar`) and opening *My Preferences*.
