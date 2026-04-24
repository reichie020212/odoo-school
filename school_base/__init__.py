from . import models


def _grant_admin_school_manager(env):
    """Grant the canonical Odoo admin user the School Manager group on first
    install. Without this, a fresh install leaves ``admin`` with no School
    group and the School app is invisible until the admin grants it to
    themselves — confusing for single-admin setups where the Odoo sysadmin
    is also the school registrar.

    Idempotent: safe to re-run; does nothing if the admin is already in the
    group. Does nothing if either record is missing (defensive for odd
    install orderings)."""
    admin = env.ref("base.user_admin", raise_if_not_found=False)
    manager = env.ref("school_base.group_school_manager", raise_if_not_found=False)
    if admin and manager and manager not in admin.group_ids:
        admin.group_ids = [(4, manager.id)]
