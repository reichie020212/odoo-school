from odoo.tests.common import TransactionCase


class TestDemoUsers(TransactionCase):
    """The school_base demo data ships non-admin accounts in two flavours:

    * Generic backend roles — ``school_user`` / ``school_reader``.
    * Persona accounts — student (Alice), guardian (Carlos), teacher
      (Maria), registrar (manager). Student & guardian are portal users
      whose ``partner_id`` must point at the matching demo partner so the
      ``school_portal`` record rules surface their own data.

    * ``demo_admin`` — admin-equivalent without ``base.group_system``.
      Has full school CRUD via Manager, plus user/contact management,
      but cannot install apps or change technical settings.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_user = cls.env.ref("school_base.demo_school_user", raise_if_not_found=False)
        cls.demo_reader = cls.env.ref("school_base.demo_school_reader", raise_if_not_found=False)
        cls.student_user = cls.env.ref("school_base.demo_user_student_alice", raise_if_not_found=False)
        cls.guardian_user = cls.env.ref("school_base.demo_user_guardian_carlos", raise_if_not_found=False)
        cls.teacher_user = cls.env.ref("school_base.demo_user_teacher_maria", raise_if_not_found=False)
        cls.registrar_user = cls.env.ref("school_base.demo_user_registrar", raise_if_not_found=False)
        cls.admin_user = cls.env.ref("school_base.demo_user_admin", raise_if_not_found=False)

    def _skip_if_no_demo(self, user):
        if not user:
            self.skipTest("Demo data not loaded; skipping demo user assertions.")

    # -- Generic backend roles -------------------------------------------------

    def test_demo_user_has_school_user_group(self):
        self._skip_if_no_demo(self.demo_user)
        self.assertEqual(self.demo_user.login, "demo_user")
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
        self.assertEqual(self.demo_reader.login, "demo_reader")
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

    # -- Persona: student (portal) --------------------------------------------

    def test_demo_student_is_portal_user_linked_to_demo_partner(self):
        self._skip_if_no_demo(self.student_user)
        student_partner = self.env.ref("school_base.student_alice_garcia")
        self.assertEqual(self.student_user.login, "demo_student")
        self.assertEqual(
            self.student_user.partner_id,
            student_partner,
            "Portal record rules in school_portal compare student_id to user.partner_id; "
            "the student demo user MUST point at the Alice Garcia partner.",
        )
        self.assertTrue(
            self.student_user.has_group("base.group_portal"),
            "Students access /my/school via the portal — they must hold base.group_portal.",
        )
        self.assertFalse(
            self.student_user.has_group("base.group_user"),
            "Students must NOT be internal users — that would expose backend menus.",
        )

    # -- Persona: guardian (portal) -------------------------------------------

    def test_demo_guardian_is_portal_user_linked_to_demo_partner(self):
        self._skip_if_no_demo(self.guardian_user)
        guardian_partner = self.env.ref("school_base.guardian_carlos_garcia")
        self.assertEqual(self.guardian_user.login, "demo_guardian")
        self.assertEqual(self.guardian_user.partner_id, guardian_partner)
        self.assertTrue(self.guardian_user.has_group("base.group_portal"))
        self.assertFalse(self.guardian_user.has_group("base.group_user"))
        self.assertTrue(
            guardian_partner.student_ward_ids,
            "Guardian Carlos must have at least one student ward so the portal "
            "rules have someone's data to surface; demo data wires Alice and Ben.",
        )

    # -- Persona: teacher (internal + School User) ----------------------------

    def test_demo_teacher_is_internal_school_user(self):
        self._skip_if_no_demo(self.teacher_user)
        self.assertEqual(self.teacher_user.login, "demo_teacher")
        self.assertTrue(self.teacher_user.has_group("base.group_user"))
        self.assertTrue(self.teacher_user.has_group("school_base.group_school_user"))
        self.assertFalse(
            self.teacher_user.has_group("school_base.group_school_manager"),
            "Teachers don't manage the academic year lifecycle — that's the registrar.",
        )
        self.assertFalse(self.teacher_user.has_group("base.group_portal"))

    # -- Persona: registrar (internal + School Manager) -----------------------

    def test_demo_registrar_is_school_manager(self):
        self._skip_if_no_demo(self.registrar_user)
        self.assertEqual(self.registrar_user.login, "demo_registrar")
        self.assertTrue(self.registrar_user.has_group("base.group_user"))
        self.assertTrue(self.registrar_user.has_group("school_base.group_school_manager"))
        self.assertTrue(
            self.registrar_user.has_group("school_base.group_school_user"),
            "Manager implies User implies Reader — registrar should walk the chain.",
        )
        self.assertFalse(
            self.registrar_user.has_group("base.group_system"),
            "Registrar is a school manager, not the Odoo sysadmin.",
        )

    # -- Persona: demo_admin (admin-equivalent without sysadmin) --------------

    def test_demo_admin_has_full_school_access(self):
        self._skip_if_no_demo(self.admin_user)
        self.assertEqual(self.admin_user.login, "demo_admin")
        self.assertTrue(self.admin_user.has_group("base.group_user"))
        self.assertTrue(
            self.admin_user.has_group("school_base.group_school_manager"),
            "demo_admin must hold School Manager so it has full CRUD on every school model.",
        )
        self.assertTrue(
            self.admin_user.has_group("school_base.group_school_user"),
            "Manager implies User (so Reader too) via the implied chain.",
        )
        self.assertTrue(
            self.admin_user.has_group("base.group_partner_manager"),
            "demo_admin manages all contacts (students, guardians, teachers).",
        )

    def test_demo_admin_cannot_reach_settings_or_install_apps(self):
        """The whole point of demo_admin: full school power, zero sysadmin power.

        In Odoo 19 the Settings root menu (``base.menu_administration``) is
        restricted to two groups — ``base.group_system`` (Administrator)
        and ``base.group_erp_manager`` (Access Rights). Holding either
        one reveals Settings → Users & Companies / Translations /
        Technical, and ``group_system`` additionally unlocks app
        install. demo_admin must hold neither.
        """
        self._skip_if_no_demo(self.admin_user)
        self.assertFalse(
            self.admin_user.has_group("base.group_system"),
            "demo_admin must NOT hold base.group_system — grants Settings access and app install.",
        )
        self.assertFalse(
            self.admin_user.has_group("base.group_erp_manager"),
            "demo_admin must NOT hold base.group_erp_manager — it's the second gate on the Settings menu.",
        )

    def test_demo_admin_cannot_see_settings_menu(self):
        """End-to-end check that the Settings menu is actually hidden.

        Group assertions cover the inputs; this covers the observable
        outcome a tester sees in the navbar. The check has to go
        through ``_visible_menu_ids`` rather than a plain
        ``ir.ui.menu.search`` — the latter only enforces ACLs / record
        rules, while the navbar runs the full filter that combines
        ``group_ids`` with the parent-cascade rule
        (``ir_ui_menu.py::_visible_menu_ids``).

        Pinned to ``debug=False``: in debug mode Odoo deliberately adds
        ``base.group_no_one`` ("Technical Features") to every user,
        which surfaces the Translations + Technical sub-menus and
        cascades the Settings parent into view. That's Odoo design, not
        a demo_admin misconfiguration.
        """
        self._skip_if_no_demo(self.admin_user)
        settings_menu = self.env.ref("base.menu_administration")
        visible_ids = self.env(user=self.admin_user)["ir.ui.menu"]._visible_menu_ids(debug=False)
        self.assertNotIn(
            settings_menu.id,
            visible_ids,
            "Settings menu must be hidden from demo_admin in normal (non-debug) mode — "
            "that's the whole point of this user.",
        )
