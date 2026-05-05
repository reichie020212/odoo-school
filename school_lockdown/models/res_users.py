from odoo import _, api, models
from odoo.exceptions import UserError

LOCKDOWN_MSG = "Self-service password changes are disabled. Contact a system administrator to update your password."


class ResUsers(models.Model):
    _inherit = "res.users"

    def preference_change_password(self):
        # UX backstop for the hidden "Change Password" button on the
        # backend My Preferences. Non-admins must not be able to swap
        # their own password — only a system administrator (Settings >
        # Users) can.
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_(LOCKDOWN_MSG))
        return super().preference_change_password()

    @api.model
    def change_password(self, old_passwd, new_passwd):
        # Catches the path used by the portal route /my/security, the
        # public RPC, and anything else that calls the documented
        # self-service "change my password" API. Admin recovery via
        # Settings > Users goes through the private _change_password
        # method instead, which we deliberately leave alone.
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_(LOCKDOWN_MSG))
        return super().change_password(old_passwd, new_passwd)
