import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from statements.models import Statement

User = get_user_model()

UPLOAD_URL = "/api/import/upload/"
LIST_URL   = "/api/import/"


class TestStatementUploadView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def _upload(self, bank="nubank", filename="fatura.csv", content=b"date,title,amount\n2026-05-01,Test,10.00\n"):
        f = io.BytesIO(content)
        f.name = filename
        return self.client.post(UPLOAD_URL, {"file": f, "bank": bank}, format="multipart")

    def test_requires_authentication(self):
        resp = self._upload()
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_file_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(UPLOAD_URL, {"bank": "nubank"}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.data)

    def test_invalid_bank_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self._upload(bank="fakebank")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.data)

    @patch("statements.views.process_statement")
    def test_successful_upload_returns_201(self, mock_process):
        self.client.force_authenticate(self.user)
        mock_stmt = Statement(
            id=1, filename="fatura.csv", bank="nubank",
            transaction_count=5, status="processed",
        )
        mock_process.return_value = mock_stmt

        resp = self._upload()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["bank"], "nubank")
        self.assertEqual(resp.data["transaction_count"], 5)
        self.assertEqual(resp.data["status"], "processed")

    @patch("statements.views.process_statement")
    def test_duplicate_filename_returns_400(self, mock_process):
        self.client.force_authenticate(self.user)
        mock_process.side_effect = ValueError("'fatura.csv' has already been imported.")

        resp = self._upload()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("already been imported", resp.data["error"])

    @patch("statements.views.process_statement")
    def test_processing_exception_returns_500(self, mock_process):
        self.client.force_authenticate(self.user)
        mock_process.side_effect = RuntimeError("Unexpected parser crash")

        resp = self._upload()
        self.assertEqual(resp.status_code, 500)
        self.assertIn("error", resp.data)

    @patch("statements.views.process_statement")
    def test_bank_lowercased(self, mock_process):
        self.client.force_authenticate(self.user)
        mock_stmt = Statement(id=1, filename="f.csv", bank="nubank", transaction_count=0, status="processed")
        mock_process.return_value = mock_stmt

        f = io.BytesIO(b"content")
        f.name = "f.csv"
        self.client.post(UPLOAD_URL, {"file": f, "bank": "NUBANK"}, format="multipart")
        # bank field is lowercased in the view before forwarding
        _, kwargs = mock_process.call_args
        self.assertEqual(kwargs.get("bank") or mock_process.call_args[0][3], "nubank")


class TestStatementListView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def test_requires_authentication(self):
        resp = self.client.get(LIST_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_user_statements(self):
        self.client.force_authenticate(self.user)
        Statement.objects.create(user=self.user, bank="nubank", filename="f1.csv", status="processed")
        Statement.objects.create(user=self.user, bank="inter", filename="f2.pdf", status="processed")

        resp = self.client.get(LIST_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_does_not_return_other_users_statements(self):
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        Statement.objects.create(user=other, bank="nubank", filename="other.csv", status="processed")

        self.client.force_authenticate(self.user)
        resp = self.client.get(LIST_URL)
        self.assertEqual(len(resp.data), 0)

    def test_limited_to_10_statements(self):
        self.client.force_authenticate(self.user)
        for i in range(15):
            Statement.objects.create(user=self.user, bank="nubank", filename=f"f{i}.csv", status="processed")

        resp = self.client.get(LIST_URL)
        self.assertEqual(len(resp.data), 10)

    def test_response_shape(self):
        self.client.force_authenticate(self.user)
        Statement.objects.create(user=self.user, bank="nubank", filename="fatura.csv", status="processed", transaction_count=5)

        resp = self.client.get(LIST_URL)
        item = resp.data[0]
        for field in ("id", "filename", "bank", "transaction_count", "status", "uploaded_at"):
            self.assertIn(field, item)
