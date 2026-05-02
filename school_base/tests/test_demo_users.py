from odoo.tests.common import TransactionCase


class TestDemoUsers(TransactionCase):
    """The school_base demo data ships two non-admin accounts so testers and
    viewers can sign in without using the all-powerful admin user. Each must
    be a real internal user (so backend menus render) and carry exactly the
    School group it advertises in its name."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_user = cls.env.ref("school_base.demo_school_user", raise_if_not_found=False)
        cls.demo_reader = cls.env.ref("school_base.demo_school_reader", raise_if_not_found=False)

    def _skip_if_no_demo(self, user):
        if not user:
            self.skipTest("Demo data not loaded; skipping demo user assertions.")

    def test_demo_user_has_school_user_group(self):
        self._skip_if_no_demo(self.demo_user)
        self.assertEqual(self.demo_user.login, "school_user")
        self.assertTrue(self.demo_user.has_group("base.group_user"), "Demo user must be an internal user.")
        self.assertTrue(
            self.demo_user.has_group("school_base.group_school_user"),
            "Demo user must hold the School User group.",
        )
        self.assertTrue(
            self.demo_user.has_group("school_base.group_school_reader"),
            "School User implies School Reader; demo user should inherit it via the implied chain.",
        )
        self.assertFalse(
            self.demo_user.has_group("school_base.group_school_manager"),
            "Demo user must NOT be a School Manager — that's the admin's role.",
        )

    def test_demo_reader_has_only_reader_group(self):
        self._skip_if_no_demo(self.demo_reader)
        self.assertEqual(self.demo_reader.login, "school_reader")
        self.assertTrue(self.demo_reader.has_group("base.group_user"), "Demo reader must be an internal user.")
        self.assertTrue(
            self.demo_reader.has_group("school_base.group_school_reader"),
            "Demo reader must hold the School Reader group.",
        )
        self.assertFalse(
            self.demo_reader.has_group("school_base.group_school_user"),
            "Demo reader must not have write access via School User.",
        )
        self.assertFalse(
            self.demo_reader.has_group("school_base.group_school_manager"),
            "Demo reader must not have manager access.",
        )

    def test_demo_users_are_not_admin(self):
        """Sanity check — these are explicitly non-admin accounts."""
        self._skip_if_no_demo(self.demo_user)
        self._skip_if_no_demo(self.demo_reader)
        self.assertFalse(self.demo_user.has_group("base.group_system"))
        self.assertFalse(self.demo_reader.has_group("base.group_system"))
