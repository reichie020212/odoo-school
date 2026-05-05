{
    "name": "School Lockdown",
    "version": "19.0.1.0.0",
    "summary": "Disable self-service password changes and the public reset-password link",
    "description": """
School Lockdown
===============

Tightens self-service authentication for the School Management System.

Changes after install:

* The "Change Password" button is removed from My Preferences for everyone
  except system administrators (``base.group_system``).
* Calling ``preference_change_password`` server-side raises a ``UserError``
  for non-admins, so a crafted RPC cannot bypass the UI.
* The ``auth_signup.reset_password`` ``ir.config_parameter`` is set to
  ``False`` so the "Reset Password" link no longer appears on the login page.

Admins keep full control: ``Settings > Users`` still has the password-change
wizard, and admins changing their own password via My Preferences is
unaffected. This module only blocks self-service password changes by
non-admin users.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Tools",
    "depends": [
        "base",
        # auth_signup must load FIRST so its data file (which calls
        # set_param('auth_signup.reset_password', 'True') via a <function>
        # tag) runs before ours. Our data file then re-runs the same call
        # with 'False' on every install/upgrade and wins.
        "auth_signup",
    ],
    "data": [
        "data/auth_signup_data.xml",
        "views/res_users_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
