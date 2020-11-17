from rest_framework import (
    generics,
    authentication,
    permissions
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from django.contrib.auth import get_user_model

from user import serializers


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = serializers.UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a token for user"""
    serializer_class = serializers.AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage updating profile user in the system"""
    serializer_class = serializers.ManageUserSerializer
    authentication_classes = [authentication.TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, ]

    def get_object(self):
        """Retrieve and return authentication user"""
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Manage change password profile user in the system"""
    serializer_class = serializers.ChangePasswordSerializer
    authentication_classes = [authentication.TokenAuthentication, ]
    permission_classes = [permissions.IsAuthenticated, ]
    queryset = get_user_model().objects.all()

    def get_object(self):
        """Retrieve and return authentication user"""
        return self.request.user
