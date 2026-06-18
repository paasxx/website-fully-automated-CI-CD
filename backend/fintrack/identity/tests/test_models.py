from django.contrib.auth import get_user_model
from django.test import TestCase

from identity.models import UserProfile

User = get_user_model()


class TestUserModel(TestCase):
    def test_str_returns_email(self):
        user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")
        self.assertEqual(str(user), "test@example.com")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_email_unique(self):
        User.objects.create_user(username="dup@example.com", email="dup@example.com", password="pass123")
        with self.assertRaises(Exception):
            User.objects.create_user(username="dup@example.com", email="dup@example.com", password="pass456")

    def test_required_fields_empty(self):
        # REQUIRED_FIELDS controls which fields are asked by createsuperuser
        self.assertEqual(User.REQUIRED_FIELDS, [])


class TestUserProfileModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def test_str_contains_email(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertIn("test@example.com", str(profile))

    def test_default_timezone(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.timezone, "America/Sao_Paulo")

    def test_optional_fields_blank_by_default(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.display_name, "")
        self.assertEqual(profile.notification_email, "")
        self.assertEqual(profile.phone, "")

    def test_one_to_one_relation(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(self.user.profile, profile)
