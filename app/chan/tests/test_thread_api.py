import os
import shutil
import tempfile

from PIL import Image

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Thread, Upvote, Downvote
from core.tests.test_models import (
    create_user, create_board
)

from chan.serializers import ThreadSerializer


# TODO ADD TEST FOR UPVOTE/DOWNVOTE SYSTEM


THREAD_URL = reverse('6chan:thread-list')


def detail_url(pk):

    return reverse('6chan:thread-detail', args=[pk])


def vote_url(type, pk):

    return reverse(f'6chan:thread-{type}-thread', args=[pk])


def create_payload(**params):

    defaults = {
        'title': 'test thread',
        'content': 'test content bla bla bla'
    }
    defaults.update(**params)

    return defaults


def create_thread(user, board, **params):

    defaults = {
        'title': 'test thread',
        'content': 'test content bla bla bla'
    }
    defaults.update(**params)

    return Thread.objects.create(user=user, board=board, **defaults)


class PublicThreadApiTests(TestCase):
    """Test publicly thread API endpoint"""

    def setUp(self):
        self.client = APIClient()

    def test_access_thread_list(self):
        """Test that accessing threads list is allowed
        wit anonymous user"""
        user = create_user()
        admin = create_user(is_admin=True)
        board = create_board(user=admin)
        create_thread(user=user, board=board)
        create_thread(
            user=user,
            title='test2 thread',
            content='test2 content',
            board=board
        )

        res = self.client.get(THREAD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        threads = Thread.objects.all()
        serializer = ThreadSerializer(threads, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_create_thread_not_allowed(self):
        """Test create a new thread with anonymous user
        is not allowed"""
        payload = create_payload()

        res = self.client.post(THREAD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        is_exists = Thread.objects.filter(
            title=payload['title'],
            content=payload['content']
        )
        self.assertFalse(is_exists)


class PrivateThreadApiTests(TestCase):
    """Test privately thread API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.admin = create_user(is_admin=True)
        self.client.force_authenticate(user=self.user)
        self.board = create_board(user=self.admin)

    def tearDown(self):
        directory = 'uploads/thread/'
        path = os.path.join(settings.MEDIA_ROOT, directory)

        shutil.rmtree(path, ignore_errors=True)

    def test_create_thread_successful(self):
        """Test that create a new thread with
        authenticated user is successful"""
        payload = create_payload(board=self.board.id)

        res = self.client.post(THREAD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Thread.objects.filter(
            user=self.user,
            title=payload['title'],
            content=payload['content']
        ).exists()
        self.assertTrue(is_exists)

    @patch('uuid.uuid4')
    def test_create_thread_with_image(self, mock_uuid):
        """Test creating a new thread with image"""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            uuid = 'test_uuid'
            mock_uuid.return_value = uuid

            image = Image.new('RGB', (100, 100))
            image.save(ntf, format='JPEG')
            ntf.seek(0)

            payload = create_payload(image=ntf, board=self.board.id)

            res = self.client.post(THREAD_URL, payload)
            file_path = os.path.join(
                '/app/' + settings.MEDIA_ROOT,
                f'uploads/thread/{uuid}.jpg'
            )

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            thread = Thread.objects.get(
                user=self.user,
                title=payload['title'],
                content=payload['content']
            )
            self.assertEqual(thread.image.path, file_path)

    def test_retrieve_thread(self):
        """Test retrieving a thread"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        url = detail_url(thread.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], thread.title)
        self.assertEqual(res.data['content'], thread.content)

    def test_update_thread(self):
        payload = create_payload(
            title='edited thread',
            content='edited content',
        )
        thread = create_thread(
            user=self.user, board=self.board
        )
        url = detail_url(thread.id)

        res = self.client.patch(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.title, payload['title'])
        self.assertEqual(thread.content, payload['content'])
        self.assertTrue(thread.is_edited)

    def test_update_other_user_thread(self):
        """Test that updating other user thread
        is not allowed"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com',
            password='testpass'
        )
        thread = create_thread(
            user=user2, board=self.board
        )
        payload = create_payload(
            title='edited thread',
            content='edited content'
        )
        url = detail_url(thread.id)

        res = self.client.patch(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(payload['title'], thread.title)
        self.assertNotEqual(payload['content'], thread.content)

    def test_upvote_thread(self):
        """Test upvoting a thread in API"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        payload = {
            'thread': thread.id
        }
        url = vote_url('upvote', thread.id)

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.upvote_thread.count(), 1)

    def test_downvote_thread(self):
        """Test downvoting a thread in API"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        payload = {'thread': thread.id, }
        url = vote_url('downvote', thread.id)

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.downvote_thread.count(), 1)

    def test_upvote_to_other_user_thread(self):
        """Test upvoting to other user thread"""
        user2 = create_user(
            username='other', email='other@gmail.com',
        )
        thread = create_thread(
            user=user2, board=self.board
        )
        url = vote_url('upvote', thread.id)
        payload = {'thread': thread.id, }

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.upvote_thread.count(), 1)

    def test_downvote_to_other_user_thread(self):
        """Test downvoting to other user thread"""
        user2 = create_user(
            username='other', email='other@gmail.com',
        )
        thread = create_thread(
            user=user2, board=self.board
        )
        url = vote_url('downvote', thread.id)
        payload = {'thread': thread.id, }

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.downvote_thread.count(), 1)

    def test_upvoting_thread_already_upvote(self):
        """Test upvoting thread that already upvoted"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        Upvote.objects.create(
            user=self.user, thread=thread
        )
        url = vote_url('upvote', thread.id)
        payload = {'thread': thread.id}

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(thread.upvote_thread.count(), 1)

    def test_downvote_thread_already_downvote(self):
        """Test upvoting thread that already upvoted"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        Downvote.objects.create(
            user=self.user, thread=thread
        )
        url = vote_url('downvote', thread.id)
        payload = {'thread': thread.id}

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(thread.downvote_thread.count(), 1)

    def test_upvote_already_downvote_same_thread(self):
        """Test that upvoting a same thread when user already
        downvoted before will deleted downvote data"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        Downvote.objects.create(
            user=self.user, thread=thread
        )
        url = vote_url('upvote', thread.id)
        payload = {'thread': thread.id}

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.downvote_thread.count(), 0)
        self.assertEqual(thread.upvote_thread.count(), 1)

    def test_downvote_already_upvote_same_thread(self):
        """Test that downvoting a same thread when user already
        upvoted before will deleted upvote data"""
        thread = create_thread(
            user=self.user, board=self.board
        )
        Upvote.objects.create(
            user=self.user, thread=thread
        )
        url = vote_url('downvote', thread.id)
        payload = {'thread': thread.id}

        res = self.client.post(url, payload)
        thread.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(thread.upvote_thread.count(), 0)
        self.assertEqual(thread.downvote_thread.count(), 1)
