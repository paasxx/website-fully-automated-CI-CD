from django.test import SimpleTestCase

from statements.parsers.btg import BTGParser
from statements.parsers.inter import InterParser
from statements.parsers.nubank import NubankParser
from statements.parsers.registry import get_parser


class TestGetParser(SimpleTestCase):
    def test_nubank(self):
        self.assertIsInstance(get_parser("nubank"), NubankParser)

    def test_inter(self):
        self.assertIsInstance(get_parser("inter"), InterParser)

    def test_btg(self):
        self.assertIsInstance(get_parser("btg"), BTGParser)

    def test_unknown_bank_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            get_parser("unknown_bank")
        self.assertIn("unknown_bank", str(ctx.exception))

    def test_case_sensitive_uppercase_raises(self):
        with self.assertRaises(ValueError):
            get_parser("Nubank")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            get_parser("")

    def test_returns_singleton(self):
        # Registry returns the same instance each call (not a new object per call)
        self.assertIs(get_parser("nubank"), get_parser("nubank"))
