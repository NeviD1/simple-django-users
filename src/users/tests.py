from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User
from .services import get_active_user_count, get_admin_emails, send_admin_daily_mail, send_mail_for_new_users


class UsersManagersTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="normal@user.com", password="foo")

        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNone(user.username)
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(email="super@user.com", password="foo")

        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertIsNone(admin_user.username)
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="super@user.com", password="foo", is_superuser=False)


class ServicesTests(TestCase):
    def setUp(self):
        User.objects.create(email="admin1@example.com", is_active=True, is_superuser=True)
        User.objects.create(email="admin2@example.com", is_active=True, is_superuser=True)
        User.objects.create(email="admin3@example.com", is_active=False, is_superuser=True)
        User.objects.create(email="user1@example.com", is_active=True)
        User.objects.create(email="user2@example.com", is_active=False)
        User.objects.create(email="user3@example.com", is_active=True)

    @patch("users.services.send_mail")
    def test_send_mail_for_new_users(self, mock_send_mail: Mock):
        test_emails = ["test1@example.com", "test2@example.com"]
        send_mail_for_new_users(test_emails)

        mock_send_mail.assert_called()

    @patch("users.services.send_mail")
    def test_send_admin_daily_mail(self, mock_send_mail: Mock):
        send_admin_daily_mail()

        mock_send_mail.assert_called()

    def test_get_active_user_count(self):
        count = get_active_user_count()

        self.assertEqual(count, 4)

    def test_get_admin_emails(self):
        admin_emails = get_admin_emails()

        self.assertEqual(len(admin_emails), 2)
        self.assertEqual(set(admin_emails), set(["admin1@example.com", "admin2@example.com"]))


class JWTTests(APITestCase):
    def test_api_jwt(self):
        url = reverse("token_obtain_pair")
        user = User.objects.create_user(email="user@example.com", password="pass")
        user.is_active = False
        user.save()

        response = self.client.post(url, {"email": "user@example.com", "password": "pass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user.is_active = True
        user.save()

        response = self.client.post(url, {"email": "user@example.com", "password": "pass"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in response.data)
        token = response.data["access"]

        me_url = reverse("me")
        headers = {"Authorization": f"Bearer {token}"}
        resp = self.client.get(me_url, headers=headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        headers = {"Authorization": "Bearer 123"}
        resp = self.client.get(me_url, headers=headers, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserViewTests(APITestCase):
    def test_get_current_user(self):
        url = reverse("me")
        user = User.objects.create(email="current@example.com", is_active=True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "current@example.com")


class UserListViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("users")
        self.user1 = User.objects.create(email="user1@example.com", is_active=True)
        self.user2 = User.objects.create(email="user2@example.com", is_active=True)
        self.client.force_authenticate(user=self.user1)

    def test_get_users(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_users(self):
        data = {"email": "user3@example.com", "password": "pass"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)

        data = [{"email": "user4@example.com", "password": "pass"}, {"email": "user5@example.com", "password": "pass"}]
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 5)

    def test_update_users(self):
        data = {"id": self.user2.id, "email": "updated@example.com", "first_name": "foo"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.email, "updated@example.com")
        self.assertEqual(self.user2.first_name, "foo")

        data = [{"id": self.user1.id, "email": "new1@example.com"}, {"id": self.user2.id, "email": "new2@example.com"}]
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, "new1@example.com")
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.email, "new2@example.com")
