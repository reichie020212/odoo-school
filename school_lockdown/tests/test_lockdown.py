from odoo.exceptions import AccessDenied, UserError
from odoo.tests.common import HttpCase, TransactionCase, tagged

LOCKDOWN_MSG = "Self-service password changes are disabled"


@tagged("post_install", "-at_install")
class TestSchoolLockdown(TransactionCase):
    """The lockdown module makes four guarantees:

    1. ``ir.config_parameter`` ``auth_signup.reset_password`` is ``'False'``
       so the public reset-password link is suppressed.
    2. The ``preference_change_password`` server method raises
       ``UserError`` for non-admins — covers the backend My Preferences
       button and any RPC that opens the wizard.
    3. The public ``change_password`` API on ``res.users`` raises
       ``UserError`` for non-admins — covers the portal ``/my/security``
       form and any direct RPC call.
    4. System administrators bypass both gates: backend self-service and
       admin-issued recovery via ``_change_password`` continue to work.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env["res.users"]
        cls.regular_user = cls.Users.create(
            {
                "name": "Lockdown Tester",
                "login": "test_lockdown_tester",
                "password": "initial-pw",
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
        self.assertIn(LOCKDOWN_MSG, str(cm.exception))

    def test_non_admin_cannot_invoke_change_password(self):
        """The portal /my/security route ultimately calls
        ``res.users.change_password(old, new)`` on the public API.
        Block at the model layer so we cover the portal AND any direct
        RPC."""
        with self.assertRaises(UserError) as cm:
            self.Users.with_user(self.regular_user).change_password("initial-pw", "new-pw")
        self.assertIn(LOCKDOWN_MSG, str(cm.exception))

    def test_admin_bypasses_lockdown_gate(self):
        """Admin must NOT hit our lockdown UserError. The parent method is
        ``@check_identity``-protected and raises an HTTP-only error when
        called outside a real request — that's expected and proves the
        admin made it past our gate."""
        admin = self.env.ref("base.user_admin")
        with self.assertRaises(UserError) as cm:
            admin.with_user(admin).preference_change_password()
        self.assertNotIn(
            LOCKDOWN_MSG,
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


@tagged("post_install", "-at_install")
class TestSchoolLockdownPortal(HttpCase):
    """End-to-end check that the portal /my/security POST cannot change a
    non-admin's password. We exercise the real HTTP route against the test
    server so the override on res.users.change_password is hit through the
    same code path users would actually use."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "Portal Lockdown Tester",
                "login": "test_lockdown_portal",
                "password": "portal-initial-pw",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )

    def test_portal_change_password_post_does_not_change_password(self):
        """A portal user POSTing to /my/security with a valid old password
        and a fresh new password must NOT have their password changed.
        Authoritative check: re-authenticate with the original password
        afterwards. The visual error message lives inside the section we
        hide via ``groups``, so we don't assert on the response body —
        the security guarantee is "no password write happened"."""
        self.authenticate("test_lockdown_portal", "portal-initial-pw")
        response = self.url_open(
            "/my/security",
            data={
                "csrf_token": self.csrf_token(),
                "op": "password",
                "old": "portal-initial-pw",
                "new1": "attempt-new-pw",
                "new2": "attempt-new-pw",
            },
        )
        self.assertEqual(response.status_code, 200)
        # Original password still authenticates → the override blocked the write.
        auth_info = self.env["res.users"].authenticate(
            {
                "type": "password",
                "login": self.portal_user.login,
                "password": "portal-initial-pw",
            },
            {"interactive": False},
        )
        self.assertEqual(
            auth_info["uid"],
            self.portal_user.id,
            "Lockdown failed: portal POST to /my/security changed the password.",
        )
        # And the attempted new password must NOT authenticate.
        # Odoo 19's authenticate() raises AccessDenied on bad creds rather
        # than returning False/None.
        with self.assertRaises(AccessDenied, msg="Lockdown failed: the attempted new password authenticates."):
            self.env["res.users"].authenticate(
                {
                    "type": "password",
                    "login": self.portal_user.login,
                    "password": "attempt-new-pw",
                },
                {"interactive": False},
            )

    def csrf_token(self):
        """Hit the security page first to scrape a fresh CSRF token from
        the rendered form. The portal controller validates it on POST."""
        page = self.url_open("/my/security").text
        marker = 'name="csrf_token" value="'
        idx = page.find(marker)
        if idx == -1:
            self.fail("Could not find CSRF token in /my/security response")
        start = idx + len(marker)
        end = page.find('"', start)
        return page[start:end]
