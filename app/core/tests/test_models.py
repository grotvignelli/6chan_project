import datetime

from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


SAMPLE_EMAIL = 'test@gmail.com'
SAMPLE_USERNAME = 'testuser'
SAMPLE_PASS = 'testpass'


class ModelTests(TestCase):
    """Test custom user model for user objects in db"""

    def test_create_user_successful(self):
        """
        Test create a new user with required fields:
        * Email
        * Username
        (with default avatar)
        """
        user = get_user_model().objects.create_user(
            email=SAMPLE_EMAIL,
            username=SAMPLE_USERNAME,
            password=SAMPLE_PASS
        )

        is_exists = get_user_model().objects.filter(
            email=SAMPLE_EMAIL,
            username=SAMPLE_USERNAME,
        ).exists()
        default_avatar_name = 'uploads/defaults/default.png'

        self.assertTrue(is_exists)
        self.assertEqual(user.email, SAMPLE_EMAIL)
        self.assertEqual(user.username, SAMPLE_USERNAME)
        self.assertEqual(user.avatar.name, default_avatar_name)
        self.assertTrue(user.check_password(SAMPLE_PASS))

    def test_create_user_with_dob(self):
        """Test create a new user with date of birth"""
        dob = datetime.date(1992, 12, 25)
        user = get_user_model().objects.create_user(
            email=SAMPLE_EMAIL,
            username=SAMPLE_USERNAME,
            date_of_birth=dob,
            password=SAMPLE_PASS
        )

        self.assertEqual(user.date_of_birth, dob)

    @patch('uuid.uuid4')
    def test_avatar_file_name(self, mock_uuid):
        """Test that image is saved in correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.avatar_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/avatar/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)

    def test_create_user_invalid_email(self):
        """Test create a new user without email is raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                username=SAMPLE_USERNAME,
                password=SAMPLE_PASS
            )

    def test_create_user_invalid_username(self):
        """Test create a new user without username is raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=SAMPLE_EMAIL,
                username=None,
                password=SAMPLE_PASS
            )

    def test_create_user_email_normalize(self):
        """Test create user email get normalized"""
        email = 'test@GMAIL.COM'
        user = get_user_model().objects.create_user(
            email=email,
            username=SAMPLE_USERNAME,
            password=SAMPLE_PASS
        )

        self.assertEqual(user.email, email.lower())

    def test_create_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            email=SAMPLE_EMAIL,
            username=SAMPLE_USERNAME,
            password=SAMPLE_PASS
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
