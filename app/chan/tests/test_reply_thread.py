from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Reply, Thread
from core.tests.test_models import (
    create_user, create_board
)


# TODO (MAYBE) ADD TEST FOR SEARCHING AND FILTERING???


REPLY_URL = reverse('6chan:reply-list')


def detail_reply_url(pk):

    return reverse('6chan:reply-detail', args=[pk])


def create_payload(**params):

    defaults = {
        'text': 'test reply',
    }
    defaults.update(**params)

    return defaults


def create_reply(user, **params):

    defaults = {
        'text': 'create reply',
    }
    defaults.update(**params)

    return Reply.objects.create(
        user=user,
        **defaults,
    )


class PublicReplyApiTests(TestCase):
    """Test publicly reply API"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_admin=True)
        self.user = create_user()
        self.board = create_board(user=self.admin)
        self.thread = Thread.objects.create(
            title='setup thread',
            content='setup content',
            user=self.user,
            board=self.board
        )

    def test_replying_to_thread_not_allowed(self):
        """Test that replying to thread with anonymous user
        is not allowed"""
        payload = create_payload()

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        is_exists = Reply.objects.filter(
            user=self.user,
            text=payload['text']
        ).exists()
        self.assertFalse(is_exists)

    def test_replying_to_reply_not_allowed(self):
        """Test that replying to reply with anonymous user
        is not allowed"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com'
        )
        reply = create_reply(user=user2, thread=self.thread)
        payload = create_payload(
            reply=reply.id
        )

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        is_exists = Reply.objects.filter(
            user=self.user,
            text=payload['text']
        ).exists()
        self.assertFalse(is_exists)


class PrivateReplyApiTests(TestCase):
    """Test privately Reply API"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_admin=True)
        self.user = create_user()
        self.board = create_board(user=self.admin)
        self.thread = Thread.objects.create(
            title='setup thread',
            content='setup content',
            user=self.user,
            board=self.board
        )
        self.client.force_authenticate(user=self.user)

    def test_reply_to_thread_successful(self):
        """Test that authenticated user replying to thread
        is successful"""
        payload = create_payload(
            thread=self.thread.id
        )

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Reply.objects.filter(
            user=self.user,
            thread=self.thread,
            text=payload['text']
        ).exists()
        self.assertTrue(is_exists)

    def test_reply_to_other_user_thread(self):
        """Test that replying to other user thread
        is successful"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com'
        )
        other_thread = Thread.objects.create(
            user=user2,
            title='test reply other thread',
            content='hello world',
            board=self.board
        )
        payload = create_payload(
            thread=other_thread.id
        )

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Reply.objects.filter(
            user=self.user,
            thread=other_thread,
            text=payload['text']
        ).exists()
        self.assertTrue(is_exists)

    def test_reply_to_reply_successful(self):
        """Test that authenticated user replying to reply
        is successful"""
        reply = create_reply(
            user=self.user, thread=self.thread
        )
        payload = create_payload(reply=reply.id)

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Reply.objects.filter(
            user=self.user,
            reply=reply,
            text=payload['text']
        ).exists()
        self.assertTrue(is_exists)

    def test_reply_to_other_user_reply(self):
        """Test that reply to other user reply
        is successful"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com'
        )
        reply = create_reply(
            user=user2, thread=self.thread
        )
        payload = create_payload(reply=reply.id)

        res = self.client.post(REPLY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Reply.objects.filter(
            user=self.user,
            reply=reply,
            text=payload['text']
        ).exists()
        self.assertTrue(is_exists)

    def test_update_reply_successful(self):
        """Test that updating a reply is successful
        for authenticated user"""
        reply = create_reply(
            user=self.user, thread=self.thread
        )
        url = detail_reply_url(reply.id)
        payload = create_payload(text='new text')

        res = self.client.patch(url, payload)
        reply.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(reply.text, payload['text'])

    def test_update_other_user_reply(self):
        """Test that updating an other user reply is
        forbidden"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com'
        )
        reply = create_reply(
            user=user2, thread=self.thread
        )
        url = detail_reply_url(reply.id)
        payload = create_payload(text='new text')

        res = self.client.patch(url, payload)
        reply.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(reply.text, payload['text'])

    def test_delete_reply_successful(self):
        """Test that deleting a reply is successful
        for authenticated user"""
        text = 'delete reply'
        reply = create_reply(
            user=self.user, thread=self.thread, text=text
        )
        url = detail_reply_url(reply.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        is_exists = Reply.objects.filter(
            user=self.user, text=text
        ).exists()
        self.assertFalse(is_exists)

    def test_delete_other_user_reply(self):
        """Test that deleting an other user reply
        is forbidden"""
        user2 = create_user(
            username='user2',
            email='user2@gmail.com'
        )
        text = 'delete reply'
        reply = create_reply(
            user=user2, thread=self.thread, text=text
        )
        url = detail_reply_url(reply.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        is_exists = Reply.objects.filter(
            user=user2, text=text
        ).exists()
        self.assertTrue(is_exists)
