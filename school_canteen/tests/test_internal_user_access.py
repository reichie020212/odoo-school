from odoo.tests.common import TransactionCase


class TestInternalUserDietaryTagAccess(TransactionCase):
    """A plain ``base.group_user`` internal user must be able to read
    ``school.canteen.dietary.tag`` records — without this ACL, opening any
    ``res.partner`` form blows up because the ORM reads
    ``canteen_allergy_tag_ids`` even when the view hides it (the read fires
    before the view's ``invisible`` directive applies)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Plain Internal User",
                "login": "test_plain_internal_canteen",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.tag = cls.env["school.canteen.dietary.tag"].create({"name": "Test Nuts", "code": "test_nuts_internal"})

    def test_internal_user_reads_dietary_tag(self):
        self.tag.with_user(self.internal_user).read(["name", "code"])

    def test_internal_user_reads_partner_with_allergy_tags(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Allergic Partner",
                "is_student": True,
                "canteen_allergy_tag_ids": [(6, 0, [self.tag.id])],
            }
        )
        partner.with_user(self.internal_user).read(["name", "canteen_allergy_tag_ids"])
