from django.contrib.auth import get_user_model
from django.test import TestCase

from identity.models import UserProfile
from identity.serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class TestRegisterSerializer(TestCase):
    def _data(self, **kwargs):
        defaults = {"email": "new@example.com", "password": "strongpass123"}
        defaults.update(kwargs)
        return defaults

    def test_valid_data_creates_user(self):
        s = RegisterSerializer(data=self._data())
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.email, "new@example.com")

    def test_password_is_hashed(self):
        s = RegisterSerializer(data=self._data())
        s.is_valid()
        user = s.save()
        self.assertTrue(user.check_password("strongpass123"))
        self.assertNotEqual(user.password, "strongpass123")

    def test_creates_user_profile(self):
        s = RegisterSerializer(data=self._data())
        s.is_valid()
        user = s.save()
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_password_shorter_than_8_invalid(self):
        s = RegisterSerializer(data=self._data(password="short"))
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_duplicate_email_invalid(self):
        User.objects.create_user(username="new@example.com", email="new@example.com", password="pass123")
        s = RegisterSerializer(data=self._data())
        self.assertFalse(s.is_valid())

    def test_optional_first_and_last_name(self):
        s = RegisterSerializer(data=self._data(first_name="Pedro", last_name="S"))
        self.assertTrue(s.is_valid())
        user = s.save()
        self.assertEqual(user.first_name, "Pedro")
        self.assertEqual(user.last_name, "S")

    def test_password_not_in_response(self):
        s = RegisterSerializer(data=self._data())
        s.is_valid()
        s.save()
        self.assertNotIn("password", s.data)


class TestUserSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")
        UserProfile.objects.create(user=self.user, timezone="America/Sao_Paulo")

    def test_read_includes_nested_profile(self):
        s = UserSerializer(self.user)
        self.assertIn("profile", s.data)
        self.assertIn("timezone", s.data["profile"])

    def test_email_is_read_only(self):
        s = UserSerializer(self.user, data={"email": "changed@example.com", "profile": {}}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")

    def test_update_first_name(self):
        s = UserSerializer(self.user, data={"first_name": "Pedro", "profile": {}}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Pedro")

    def test_update_profile_timezone(self):
        s = UserSerializer(self.user, data={"profile": {"timezone": "America/New_York"}}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.timezone, "America/New_York")

    def test_update_profile_display_name(self):
        s = UserSerializer(self.user, data={"profile": {"display_name": "pedro.dev"}}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, "pedro.dev")
