from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Custom user model"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'date_of_birth', 'password', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6
            },
        }

    def create(self, validated_data):
        """Override default create method to support hashing password"""
        return get_user_model().objects.create_user(**validated_data)


class ManageUserSerializer(serializers.ModelSerializer):
    """Serializer for custom user model
    (without password field)
    """

    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'date_of_birth', 'avatar']


class ChangePasswordSerializer(serializers.ModelSerializer):
    """Serializer for change-password endpoint"""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=6
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ['old_password', 'new_password', 'confirm_password']

    def validate(self, attrs):
        """Validating new_password and confirm_password is same"""
        if attrs['new_password'] != attrs['confirm_password']:
            msg = _('Password fields didn\'t match')
            raise serializers.ValidationError({'password': msg})

        return attrs

    def validate_old_password(self, value):
        """Validating user old password"""
        user = self.context.get('request').user

        if not user.check_password(value):
            msg = _('Old password is not correct')
            raise serializers.ValidationError({'old_password': msg})

        return value

    def update(self, instance, validated_data):
        """Update a new password for user"""
        instance.set_password(validated_data['new_password'])
        instance.save()

        return instance


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user signin (to get a token)"""
    username = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate user"""
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs
