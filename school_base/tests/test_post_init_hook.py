from odoo.tests.common import TransactionCase


class TestPostInitHook(TransactionCase):
    """The post_init_hook grants the admin user School Manager on install.
    We can't directly re-run the hook in a test (installation is a one-shot
    event), but we can verify the expected end state: on a running install,
    base.user_admin must be in group_school_manager."""

    def test_admin_is_school_manager(self):
        admin = self.env.ref("base.user_admin")
        manager = self.env.ref("school_base.group_school_manager")
        self.assertIn(
            manager,
            admin.group_ids,
            f"Expected base.user_admin to be in school_base.group_school_manager "
            f"via the post_init_hook; got groups: {admin.group_ids.mapped('id')!r}",
        )

    def test_hook_is_idempotent(self):
        """Running the hook again must not duplicate the group membership or
        raise."""
        from odoo.addons.school_base import _grant_admin_school_manager

        admin = self.env.ref("base.user_admin")
        manager = self.env.ref("school_base.group_school_manager")
        before_count = len(admin.group_ids.filtered(lambda g: g == manager))
        _grant_admin_school_manager(self.env)
        after_count = len(admin.group_ids.filtered(lambda g: g == manager))
        self.assertEqual(before_count, after_count)
        self.assertEqual(after_count, 1)
