from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from identity.models import UserProfile

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
ME_URL       = "/api/auth/me/"


class TestRegisterView(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        resp = self.client.post(REGISTER_URL, {"email": "new@example.com", "password": "strongpass123"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_returns_email(self):
        resp = self.client.post(REGISTER_URL, {"email": "new@example.com", "password": "strongpass123"})
        self.assertEqual(resp.data["email"], "new@example.com")

    def test_register_does_not_return_password(self):
        resp = self.client.post(REGISTER_URL, {"email": "new@example.com", "password": "strongpass123"})
        self.assertNotIn("password", resp.data)

    def test_register_duplicate_email_returns_400(self):
        User.objects.create_user(username="dup@example.com", email="dup@example.com", password="pass123")
        resp = self.client.post(REGISTER_URL, {"email": "dup@example.com", "password": "strongpass123"})
        self.assertEqual(resp.status_code, 400)

    def test_register_weak_password_returns_400(self):
        resp = self.client.post(REGISTER_URL, {"email": "new@example.com", "password": "short"})
        self.assertEqual(resp.status_code, 400)

    def test_register_no_auth_required(self):
        # AllowAny — unauthenticated request must succeed
        resp = self.client.post(REGISTER_URL, {"email": "open@example.com", "password": "openpass123"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class TestUserDetailView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="test@example.com", email="test@example.com", password="pass123",
            first_name="Pedro", last_name="S",
        )
        UserProfile.objects.create(user=self.user)

    def test_get_requires_auth(self):
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_current_user(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["email"], "test@example.com")
        self.assertIn("profile", resp.data)

    def test_put_requires_auth(self):
        resp = self.client.put(ME_URL, {"first_name": "New", "profile": {}}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_updates_first_name(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(ME_URL, {"first_name": "Novo", "profile": {}}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Novo")

    def test_put_email_is_readonly(self):
        self.client.force_authenticate(self.user)
        self.client.put(ME_URL, {"email": "changed@example.com", "profile": {}}, format="json")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")

    def test_put_updates_profile_timezone(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(ME_URL, {"profile": {"timezone": "America/New_York"}}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.timezone, "America/New_York")

    def test_get_does_not_expose_other_users_data(self):
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        UserProfile.objects.create(user=other)
        self.client.force_authenticate(self.user)
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.data["email"], "test@example.com")
