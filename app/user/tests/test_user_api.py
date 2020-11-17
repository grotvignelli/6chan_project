import datetime
import tempfile
import os
import shutil

from unittest.mock import patch
from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APIClient


SIGNUP_USER_URL = reverse('user:signup')
TOKEN_URL = reverse('user:signin')
PROFILE_URL = reverse('user:profile')
CHANGE_PASSWORD_URL = reverse('user:change-password')


def create_payload(**params):
    defaults = {
        'email': 'test@gmail.com',
        'username': 'testuser',
        'password': 'testpass'
    }
    defaults.update(**params)

    return defaults


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test publicly user API"""

    def setUp(self):
        self.client = APIClient()

    def tearDown(self):
        directory = 'uploads/avatar'
        path = os.path.join(settings.MEDIA_ROOT, directory)

        shutil.rmtree(path, ignore_errors=True)

    def test_create_user_successful(self):
        """Test creating a new user in API is successful"""
        payload = create_payload()

        res = self.client.post(SIGNUP_USER_URL, payload)
        user = get_user_model().objects.get(
            email=payload['email'],
            username=payload['username']
        )
        default_avatar_name = 'uploads/defaults/default.png'

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user.email, payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertEqual(user.avatar.name, default_avatar_name)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_with_dob(self):
        """Test creating a new user in API with date of birth"""
        payload = create_payload(
            date_of_birth=datetime.date(1992, 12, 25),
        )

        res = self.client.post(SIGNUP_USER_URL, payload)
        user = get_user_model().objects.get(
            email=payload['email'],
            username=payload['username']
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user.date_of_birth, payload['date_of_birth'])

    @patch('uuid.uuid4')
    def test_create_user_with_avatar(self, mock_uuid):
        """Test creating a new user in API with avatar"""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            uuid = 'test-uuid'
            mock_uuid.return_value = uuid

            image = Image.new('RGB', (100, 100))
            image.save(ntf, format='JPEG')
            ntf.seek(0)

            payload = create_payload(avatar=ntf)
            res = self.client.post(
                SIGNUP_USER_URL, payload, format='multipart'
            )
            user = get_user_model().objects.get(
                email=payload['email'],
                username=payload['username']
            )
            filepath = os.path.join(
                '/app/' + settings.MEDIA_ROOT,
                f'uploads/avatar/{uuid}.jpg'
            )

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertIn('avatar', res.data)
            self.assertEqual(user.avatar.path, filepath)

    def test_create_user_invalid_email(self):
        """Test creating a new user with invalid payload
        (email blank)"""
        payload = create_payload(email='')

        res = self.client.post(SIGNUP_USER_URL, payload)
        is_exists = get_user_model().objects.filter(
            email=payload['email'],
            username=payload['username']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(is_exists)

    def test_create_user_invalid_username(self):
        """Test creating a new user with invalid payload
        (email blank)"""
        payload = create_payload(username='')

        res = self.client.post(SIGNUP_USER_URL, payload)
        is_exists = get_user_model().objects.filter(
            email=payload['email'],
            username=payload['username']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(is_exists)

    def test_create_with_exists_user(self):
        """Test creating a new user with existing user
        raises 400 status code"""
        payload = create_payload()
        create_user(**payload)

        res = self.client.post(SIGNUP_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_too_short(self):
        """Test creating a new user with password less than 6 character
        raises 400 status code"""
        payload = create_payload(password='wr')

        res = self.client.post(SIGNUP_USER_URL, payload)
        is_exists = get_user_model().objects.filter(
            email=payload['email'],
            username=payload['username']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(is_exists)

    def test_create_token_for_user(self):
        """Test create a token for authenticated user"""
        payload = create_payload()
        create_user(**payload)

        res = self.client.post(TOKEN_URL, {
            'username': payload['username'],
            'password': payload['password'],
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_with_invalid_credentials(self):
        """Test create a token for user with invalid credentials"""
        create_user(**create_payload())
        payload = {
            'username': 'testuser',
            'password': 'wrong'
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_no_user(self):
        """Test that creating token with no user existing
        is raises 400 status code"""
        payload = {
            'username': 'testuser',
            'password': 'testpass'
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_missing_fields(self):
        """Test that creating token with missing fields required
        is raises error"""
        res = self.client.post(TOKEN_URL, {'username': 'user', 'password': ''})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_profile_unauthorized(self):
        """Test retrieve user profile with no authenticated user"""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test access private user API (with authenticated user)"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(**create_payload())
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        directory = 'uploads/avatar'
        path = os.path.join(settings.MEDIA_ROOT, directory)

        shutil.rmtree(path, ignore_errors=True)

    def test_retrieve_user_profile(self):
        """Test that retrieving user profile with authenticated user"""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], self.user.username)
        self.assertEqual(res.data['email'], self.user.email)

    def test_post_method_not_allowed(self):
        """Test that POST method on user profile endpoint is not allowed"""
        res = self.client.post(PROFILE_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile successful"""
        payload = {
            'username': 'newname',
            'email': 'newemail@gmail.com'
        }

        res = self.client.patch(PROFILE_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.username, payload['username'])
        self.assertEqual(self.user.email, payload['email'])

    @patch('uuid.uuid4')
    def test_update_avatar_user(self, mock_uuid):
        """Test updating avatar profile user is successful"""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            uuid = 'test-uuid'
            mock_uuid.return_value = uuid

            image = Image.new('RGB', (100, 100))
            image.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.patch(
                PROFILE_URL, {'avatar': ntf}, format='multipart'
            )
            filename = f'uploads/avatar/{uuid}.jpg'
            self.user.refresh_from_db()

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(self.user.avatar.name, filename)

    def test_update_password_not_allowed(self):
        """Test that updating password in profile endpoint is not allowed"""
        new_pass = 'newpass'
        self.client.patch(
            PROFILE_URL, {'password': new_pass}
        )
        self.user.refresh_from_db()

        self.assertFalse(self.user.check_password(new_pass))
        # TODO how to make response status code to be 400 bad request

    def test_change_password_endpoint(self):
        """Test that change password in change-password endpoint is worked"""
        payload = {
            'old_password': 'testpass',
            'new_password': 'newpass',
            'confirm_password': 'newpass'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload['new_password']))
        self.assertNotIn('new_password', res.data)
        self.assertNotIn('confirm_password', res.data)

    def test_change_password_invalid_old_password(self):
        """Test that change password with invalid old password
        is raises error"""
        payload = {
            'old_password': 'wrong',
            'new_password': 'newpass',
            'confirm_password': 'newpass'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(payload['new_password']))

    def test_change_password_invalid_confirm_password(self):
        """Test that change password with different confirm password
        is raises error"""
        payload = {
            'old_password': 'testpass',
            'new_password': 'newpass',
            'confirm_password': 'wrong'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(payload['new_password']))

    def test_change_password_too_short(self):
        """Test that change password with less than 6 character
        is raises error"""
        payload = {
            'old_password': 'testpass',
            'new_password': 'pw',
            'confirm_password': 'pw'
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(payload['new_password']))
