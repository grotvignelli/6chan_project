from rest_framework import (
    viewsets, permissions, authentication
)

from chan.serializers import (
    BoardSerializer, ThreadSerializer
)

from core.models import Board, Thread


class ThreadPermissions(permissions.BasePermission):
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

    def get_permissions(self):
        """Return permission based on action"""

        if self.action == 'list':
            permission_classes = [permissions.AllowAny, ]
        else:
            permission_classes = [
                permissions.IsAuthenticated, ThreadPermissions
            ]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create and save thread"""
        serializer.save(user=self.request.user)
