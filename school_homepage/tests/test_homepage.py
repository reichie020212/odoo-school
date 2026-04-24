from odoo.tests import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestSchoolHomepage(HttpCase):
    def test_root_returns_200(self):
        response = self.url_open("/")
        self.assertEqual(response.status_code, 200)

    def test_root_contains_school_name(self):
        response = self.url_open("/")
        # Company name defaults to "YourCompany" on a fresh DB but could be anything.
        self.assertIn(self.env.company.name, response.text)

    def test_root_has_portal_cta(self):
        response = self.url_open("/")
        self.assertIn("/my", response.text)
        self.assertIn("/web", response.text)

    def test_root_renders_stats(self):
        response = self.url_open("/")
        # The stats section labels should appear in the rendered body.
        for label in ("Students", "Teachers", "Classrooms", "Courses", "Library Books"):
            self.assertIn(label, response.text)
