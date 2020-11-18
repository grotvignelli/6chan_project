from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Board

from core.tests.test_models import create_user

from chan.serializers import BoardSerializer


def detail_url(pk):

    return reverse('6chan:board-detail', args=[pk])


def create_payload(**params):

    defaults = {
        'name': 'politic',
        'code': 'pl',
    }
    defaults.update(**params)

    return defaults


def create_board(user, **params):

    return Board.objects.create(user=user, **params)


BOARD_URL = reverse('6chan:board-list')


class PublicBoardApiTests(TestCase):
    """Test publicly board API endpoint
    (with anonymous user)"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_admin=True)

    def test_create_board_not_allowed(self):
        """Test creating a board with anonymous user
        is not allowed"""
        payload = create_payload()

        res = self.client.post(BOARD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        is_exists = Board.objects.filter(
            name=payload['name'],
            code=payload['code']
        )
        self.assertFalse(is_exists)

    def test_access_board_list(self):
        """Test access board list with anonymous user
        is allowed"""
        create_board(user=self.admin)
        create_board(
            user=self.admin,
            name='not safe for working',
            code='nsfw'
        )

        res = self.client.get(BOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        boards = Board.objects.all()
        serializer = BoardSerializer(boards, many=True)
        self.assertEqual(res.data, serializer.data)


class PrivateBoardApiTests(TestCase):
    """Test privately board API endpoint
    (with authenticated user)"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.admin = create_user(is_admin=True)
        self.client.force_authenticate(user=self.user)

    def test_create_board_not_allowed(self):
        """Test creating a new board with authenticated user
        is not allowed"""
        payload = create_payload()

        res = self.client.post(BOARD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        is_exists = Board.objects.filter(
            name=payload['name'],
            code=payload['code']
        )
        self.assertFalse(is_exists)

    def test_access_board_list(self):
        """Test access board list with anonymous user
        is allowed"""
        create_board(user=self.admin)
        create_board(
            user=self.admin,
            name='not safe for working',
            code='nsfw'
        )

        res = self.client.get(BOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        boards = Board.objects.all()
        serializer = BoardSerializer(boards, many=True)
        self.assertEqual(res.data, serializer.data)


class BoardAdminApiTests(TestCase):
    """Test access board API with admin user"""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_admin=True)
        self.client.force_authenticate(user=self.admin)

    def test_create_board_successful(self):
        """Test creating a new board successful"""
        payload = create_payload()

        res = self.client.post(BOARD_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        is_exists = Board.objects.filter(
            user=self.admin,
            name=payload['name']
        ).exists()
        self.assertTrue(is_exists)

    def test_access_board_list(self):
        """Test access board list with anonymous user
        is allowed"""
        create_board(
            user=self.admin,
            name='graphic design',
            code='gd'
        )
        create_board(
            user=self.admin,
            name='not safe for working',
            code='nsfw'
        )

        res = self.client.get(BOARD_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        boards = Board.objects.all()
        serializer = BoardSerializer(boards, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_delete_board(self):
        """Test deleting a board successful"""
        payload = create_payload()
        board = create_board(user=self.admin, **payload)
        url = detail_url(board.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        is_exists = Board.objects.filter(
            user=self.admin,
            name=payload['name']
        ).exists()
        self.assertFalse(is_exists)
