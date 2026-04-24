from odoo.tests.common import TransactionCase


class TestInternalUserCatalogAccess(TransactionCase):
    """A plain ``base.group_user`` internal user (no School groups) must be able to
    read catalog / structural records that are referenced from ``res.partner``
    extensions. Otherwise Odoo's default flows (Contacts, Sales, HR) break on
    any install that has School modules enabled — opening a partner form
    triggers reads on ``student_classroom_id`` / ``student_academic_year_id``
    that would fail the ACL."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Plain Internal User",
                "login": "test_plain_internal_base",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.year = cls.env["school.academic.year"].create(
            {
                "name": "Test Year",
                "code": "INT-Y",
                "date_start": "2099-08-01",
                "date_end": "2100-05-31",
            }
        )
        cls.term = cls.env["school.academic.term"].create(
            {
                "name": "Test Term",
                "code": "INT-T",
                "academic_year_id": cls.year.id,
                "date_start": "2099-08-01",
                "date_end": "2099-12-31",
            }
        )
        cls.classroom = cls.env["school.classroom"].create(
            {
                "name": "Test Classroom",
                "code": "INTCR",
                "grade_level": "10",
                "academic_year_id": cls.year.id,
            }
        )

    def test_internal_user_reads_academic_year(self):
        self.year.with_user(self.internal_user).read(["name", "code"])

    def test_internal_user_reads_academic_term(self):
        self.term.with_user(self.internal_user).read(["name", "code"])

    def test_internal_user_reads_classroom(self):
        self.classroom.with_user(self.internal_user).read(["name", "code", "grade_level"])

    def test_internal_user_reads_partner_with_student_refs(self):
        """The real regression — opening a res.partner form as an internal
        user must not blow up because of the student_classroom_id /
        student_academic_year_id fields inherited from school_base."""
        student = self.env["res.partner"].create(
            {
                "name": "Test Student Partner",
                "is_student": True,
                "student_classroom_id": self.classroom.id,
            }
        )
        student.with_user(self.internal_user).read(
            ["name", "is_student", "student_classroom_id", "student_academic_year_id"]
        )
