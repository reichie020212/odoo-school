import psycopg2
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestBookCopy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Book = cls.env["school.library.book"]
        cls.Copy = cls.env["school.library.book.copy"]

    def _make_book(self, **overrides):
        defaults = {"title": "Test Book"}
        defaults.update(overrides)
        return self.Book.create(defaults)

    def _make_copy(self, book=None, **overrides):
        defaults = {"book_id": (book or self._make_book()).id, "barcode": "TEST-001"}
        defaults.update(overrides)
        return self.Copy.create(defaults)

    def test_create_copy(self):
        c = self._make_copy()
        self.assertEqual(c.state, "available")

    @mute_logger("odoo.sql_db")
    def test_barcode_unique(self):
        book = self._make_book(title="Dup Book")
        self._make_copy(book=book, barcode="TEST-DUP")
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_copy(book=book, barcode="TEST-DUP")
            self.env.flush_all()

    @mute_logger("odoo.sql_db")
    def test_isbn_unique(self):
        self._make_book(title="ISBN A", isbn="TEST-ISBN")
        with self.assertRaises(psycopg2.IntegrityError), self.cr.savepoint():
            self._make_book(title="ISBN B", isbn="TEST-ISBN")
            self.env.flush_all()

    def test_counts_update(self):
        book = self._make_book()
        self._make_copy(book=book, barcode="C1")
        self._make_copy(book=book, barcode="C2")
        book.invalidate_recordset(["copy_count", "available_count"])
        self.assertEqual(book.copy_count, 2)
        self.assertEqual(book.available_count, 2)
