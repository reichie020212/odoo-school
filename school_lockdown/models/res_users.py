from odoo import _, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    def preference_change_password(self):
        # Server-side backstop for the hidden "Change Password" button on
        # My Preferences. Non-admins must not be able to swap their own
        # password — only a system administrator (Settings > Users) can.
        if not self.env.user.has_group("base.group_system"):
            raise UserError(
                _("Self-service password changes are disabled. Contact a system administrator to update your password.")
            )
        return super().preference_change_password()
