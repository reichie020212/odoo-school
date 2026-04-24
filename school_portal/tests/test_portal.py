from odoo.tests import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestSchoolPortal(HttpCase):
    def test_portal_page_anonymous_redirects(self):
        """Anonymous users should be redirected to /web/login on /my/school."""
        response = self.url_open("/my/school", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 401))

    def test_portal_page_authenticated(self):
        """An authenticated portal user should get a 200 on /my/school."""
        # Promote demo.portal user's partner to a student so we have data to show.
        portal_user = self.env.ref("base.demo_user0", raise_if_not_found=False)
        if not portal_user:
            self.skipTest("No portal demo user present in this environment")
        portal_user.partner_id.is_student = True
        self.authenticate(portal_user.login, portal_user.login)
        response = self.url_open("/my/school")
        self.assertEqual(response.status_code, 200)
        self.assertIn("My School", response.text)
