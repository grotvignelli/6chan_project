from django.utils.translation import ugettext_lazy as _

from rest_framework import (
    viewsets, permissions, authentication, status
)
from rest_framework.decorators import action
from rest_framework.response import Response

from chan.serializers import (
    BoardSerializer, ThreadSerializer,
    UpvoteSerializer, DownvoteSerializer,
    ReplySerializer
)

from core.models import Board, Thread, Reply


class ObjectPermissions(permissions.BasePermission):
    """Giving an appropriate permission for thread"""

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class BoardViewSet(viewsets.ModelViewSet):
    """Viewset for manage board in API"""
    serializer_class = BoardSerializer
    authentication_classes = [authentication.TokenAuthentication, ]
    queryset = Board.objects.all()

    def get_permissions(self):
        """Return permission for viewset based on action"""

        if self.action == 'list':
            permission_classes = [permissions.AllowAny, ]
        else:
            permission_classes = [permissions.IsAdminUser, ]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create and save board"""
        serializer.save(user=self.request.user)


class ManageThreadViewSet(viewsets.ModelViewSet):
    """Viewset for manage thread in API"""
    serializer_class = ThreadSerializer
    authentication_classes = [authentication.TokenAuthentication, ]
    queryset = Thread.objects.all()

    def _params_to_int(self, qs):
        """Convert params string to integer"""
        return [int(str_id) for str_id in qs.split(',')]

    def perform_create(self, serializer):
        """Create and save thread"""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Return appropriate queryset"""
        board = self.request.query_params.get('board')
        queryset = self.queryset

        if board:
            board_id = self._params_to_int(board)
            queryset = queryset.filter(board__id__in=board_id)

        return queryset.order_by('-reply_to_thread__date_created')

    def get_permissions(self):
        """Return permission based on action"""
        action = [
            'list', 'retrieve',
            'upvote_thread', 'downvote_thread',
            'reply_to_thread'
        ]

        if self.action in action:
            permission_classes = [permissions.AllowAny, ]
        else:
            permission_classes = [
                permissions.IsAuthenticated, ObjectPermissions
            ]

        return [permission() for permission in permission_classes]

    @action(methods=['post'], detail=True, url_path='upvote-thread')
    def upvote_thread(self, request, pk=None):
        """Upvoting the thread"""
        thread = self.get_object()
        upvote_user_id = [
            vote.user.id for vote in thread.upvote_thread.all()
        ]
        downvote_user_id = [
            vote.user.id for vote in thread.downvote_thread.all()
        ]
        serializer = UpvoteSerializer(data=request.data)
        msg = _('You\'ve done upvoting the thread!')

        if serializer.is_valid():

            if request.user.id in upvote_user_id:
                thread.upvote_thread.filter(
                    user=request.user
                ).delete()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )

            if request.user.id in downvote_user_id:
                thread.downvote_thread.filter(
                    user=request.user
                ).delete()

                serializer.save(user=request.user)
                return Response({'message': msg})

            serializer.save(user=request.user)
            return Response({'message': msg})

        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['post'], detail=True, url_path='downvote-thread')
    def downvote_thread(self, request, pk=None):
        """Upvoting the thread"""
        thread = self.get_object()
        upvote_user_id = [
            vote.user.id for vote in thread.upvote_thread.all()
        ]
        downvote_user_id = [
            vote.user.id for vote in thread.downvote_thread.all()
        ]
        serializer = DownvoteSerializer(data=request.data)
        msg = _('You\'ve done downvoting the thread!')

        if serializer.is_valid():

            if request.user.id in downvote_user_id:
                thread.downvote_thread.filter(
                    user=request.user
                ).delete()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )

            if request.user.id in upvote_user_id:
                thread.upvote_thread.filter(
                    user=request.user
                ).delete()

                serializer.save(user=request.user)
                return Response({'message': msg})

            serializer.save(user=request.user)
            return Response({'message': msg})

        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


class ManageReplyViewSet(viewsets.ModelViewSet):
    """Viewset for manage Reply in API"""
    authentication_classes = [authentication.TokenAuthentication, ]
    serializer_class = ReplySerializer
    queryset = Reply.objects.all()

    def perform_create(self, serializer):
        """Create and save reply"""
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """Return permission based on action"""
        actions = ['list', 'retrieve']

        if self.action in actions:
            permission_classes = [permissions.AllowAny, ]
        else:
            permission_classes = [
                permissions.IsAuthenticated, ObjectPermissions
            ]

        return [permission() for permission in permission_classes]
