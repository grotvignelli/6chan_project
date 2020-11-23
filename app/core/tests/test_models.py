import datetime

from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import (
    Board, Thread, Upvote, Downvote, Reply,
    avatar_file_path, thread_img_file_path
)


SAMPLE_EMAIL = 'test@gmail.com'
SAMPLE_USERNAME = 'testuser'
SAMPLE_PASS = 'testpass'


def create_user(is_admin=False, **params):

    defaults = {
        'email': 'test@gmail.com',
        'username': 'testuser',
        'password': 'testpass'
    }
    defaults.update(**params)

    if is_admin:
        payload = {
            'email': 'admin@gmail.com',
            'username': 'admin',
            'password': 'admin'
        }
        payload.update(**params)

        return get_user_model().objects.create_superuser(**payload)

    return get_user_model().objects.create_user(**defaults)


def create_board(user, **params):

    defaults = {
        'name': 'test board',
        'code': 'tb'
    }
    defaults.update(**params)

    return Board.objects.create(user=user, **defaults)


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
        file_path = avatar_file_path(None, 'myimage.jpg')

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


class ChanModelTests(TestCase):
    """Testing for chan app model"""

    def setUp(self):
        self.admin = create_user(is_admin=True)
        self.user = create_user(
            username='setUp user',
            email='setup@gmail.com'
        )
        self.board = create_board(
            user=self.admin,
            name='test board',
            code='tb'
        )
        self.thread = Thread.objects.create(
            user=self.user,
            title='setup thread',
            content='setup content',
            board=self.board
        )

    def test_create_board_in_db(self):
        """Test creating a new board in database"""
        name = 'politic'
        code = 'pl'
        board = Board.objects.create(
            name=name,
            code=code,
            user=self.admin
        )

        self.assertEqual(str(board), name)
        is_exists = Board.objects.filter(
            user=self.admin,
            code=code
        ).exists()
        self.assertTrue(is_exists)

    def test_create_thread_in_db(self):
        """Test create a new thread in database"""
        title = 'Test thread'
        content = 'Test content bla bla bla'
        thread = Thread.objects.create(
            title=title,
            content=content,
            user=self.user,
            board=self.board
        )

        self.assertEqual(str(thread), title)
        is_exists = Thread.objects.filter(
            user=self.user,
            title=title,
            content=content
        ).exists()
        self.assertTrue(is_exists)

    @patch('uuid.uuid4')
    def test_thread_img_file_path(self, mock_uuid):
        """Test thread image upload file path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = thread_img_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/thread/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)

    def test_add_upvote_to_thread(self):
        """Test upvote to the thread"""
        Upvote.objects.create(
            user=self.user,
            thread=self.thread
        )

        self.assertEqual(self.thread.upvote_thread.count(), 1)

    def test_add_downvote_to_thread(self):
        """Test downvote to the thread"""
        Downvote.objects.create(
            user=self.user,
            thread=self.thread
        )

        self.assertEqual(self.thread.downvote_thread.count(), 1)

    def test_create_reply(self):
        """Test create a reply in the db"""
        text = 'test reply'
        reply = Reply.objects.create(
            user=self.user,
            text=text,
            thread=self.thread
        )

        self.assertEqual(str(reply), text)
        is_exists = self.thread.reply_to_thread.filter(
            user=self.user,
            text=text
        ).exists()
        self.assertTrue(is_exists)

    def test_create_reply_to_reply(self):
        user2 = create_user(
            username='user2',
            email='user2@gmail.com',
        )
        reply = Reply.objects.create(
            user=self.user,
            text='text text',
            thread=self.thread
        )
        text = 'test reply to reply'
        reply_to_reply = Reply.objects.create(
            user=user2,
            text=text,
            reply=reply
        )

        self.assertEqual(str(reply_to_reply), text)
        is_exists = reply.reply_to_reply.filter(
            user=user2,
            text=text
        ).exists()
        self.assertTrue(is_exists)
