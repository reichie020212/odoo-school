from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSchoolLockdown(TransactionCase):
    """The lockdown module makes three guarantees:

    1. ``ir.config_parameter`` ``auth_signup.reset_password`` is ``'False'``
       so the public reset-password link is suppressed.
    2. The ``preference_change_password`` server method raises ``UserError``
       for non-admins, blocking any RPC that bypasses the hidden button.
    3. System administrators bypass the gate — they continue down the
       parent's code path (which is itself ``@check_identity``-protected
       for HTTP, but our lockdown does not interfere).
    """

    LOCKDOWN_MSG = "Self-service password changes are disabled"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env["res.users"]
        cls.regular_user = cls.Users.create(
            {
                "name": "Lockdown Tester",
                "login": "test_lockdown_tester",
            }
        )

    def test_reset_password_icp_disabled(self):
        """auth_signup reads this ICP as a string compared to 'True'."""
        value = self.env["ir.config_parameter"].sudo().get_param("auth_signup.reset_password")
        self.assertEqual(
            value,
            "False",
            "school_lockdown must seed auth_signup.reset_password='False' to suppress the login-page reset link.",
        )

    def test_non_admin_cannot_invoke_preference_change_password(self):
        with self.assertRaises(UserError) as cm:
            self.regular_user.with_user(self.regular_user).preference_change_password()
        self.assertIn(self.LOCKDOWN_MSG, str(cm.exception))

    def test_admin_bypasses_lockdown_gate(self):
        """Admin must NOT hit our lockdown UserError. The parent method is
        ``@check_identity``-protected and raises an HTTP-only error when
        called outside a real request — that's expected and proves the
        admin made it past our gate. If our gate had fired, the message
        would be the lockdown one instead."""
        admin = self.env.ref("base.user_admin")
        with self.assertRaises(UserError) as cm:
            admin.with_user(admin).preference_change_password()
        self.assertNotIn(
            self.LOCKDOWN_MSG,
            str(cm.exception),
            "Admin must bypass the lockdown gate; only the framework's identity check should fire here.",
        )

    def test_admin_can_still_change_other_users_password(self):
        """Admin recovery path: Settings > Users uses a separate wizard
        that writes ``password`` directly via ``_change_password``. That
        path must not be blocked, otherwise the system has no recovery."""
        admin = self.env.ref("base.user_admin")
        target = self.regular_user.with_user(admin)
        target._change_password("admin-issued-recovery-pw")
        # Re-authenticate to confirm the new password took effect end-to-end.
        # Odoo 19 returns auth_info (dict) from authenticate() rather than uid.
        auth_info = self.Users.authenticate(
            {
                "type": "password",
                "login": self.regular_user.login,
                "password": "admin-issued-recovery-pw",
            },
            {"interactive": False},
        )
        self.assertEqual(auth_info["uid"], self.regular_user.id)
