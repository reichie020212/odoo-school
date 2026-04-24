from odoo.tests.common import TransactionCase


class TestSchoolCommsTemplates(TransactionCase):
    def test_templates_installed(self):
        for xmlid in (
            "school_comms.mail_template_fee_invoice_ready",
            "school_comms.mail_template_report_card_final",
            "school_comms.mail_template_exam_published",
        ):
            template = self.env.ref(xmlid, raise_if_not_found=False)
            self.assertTrue(template, f"Missing mail template {xmlid}")
            self.assertEqual(template._name, "mail.template")
            self.assertTrue(template.subject)
            self.assertTrue(template.body_html)

    def test_automations_installed(self):
        for xmlid in (
            "school_comms.automation_fee_invoice_notify",
            "school_comms.automation_report_card_final_notify",
            "school_comms.automation_exam_published_notify",
        ):
            rule = self.env.ref(xmlid, raise_if_not_found=False)
            self.assertTrue(rule, f"Missing automation rule {xmlid}")
            self.assertEqual(rule._name, "base.automation")

    def test_template_renders_against_demo_enrollment(self):
        enrollment = self.env.ref("school_fees.enrollment_alice_g9_s1", raise_if_not_found=False)
        if not enrollment:
            self.skipTest("Demo fee enrollment not available")
        template = self.env.ref("school_comms.mail_template_fee_invoice_ready")
        rendered = template._render_field("body_html", enrollment.ids)
        body = rendered[enrollment.id]
        self.assertIn(enrollment.student_id.display_name, body)
        self.assertIn(enrollment.structure_id.name, body)
