from rest_framework import serializers

from core.models import (
    Board, Thread, Upvote, Downvote, Reply
)


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for board model"""

    class Meta:
        model = Board
        fields = ['id', 'name', 'code', 'thread']
        read_only_fields = ['id', ]


class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for thread model"""
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all()
    )

    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'content', 'image',
            'date_created', 'reply_to_thread', 'board',
            'upvote_thread', 'downvote_thread',
            'is_edited'
        ]
        read_only_fields = ['id', 'is_edited', 'reply_to_thread']

    def update(self, instance, validated_data):
        """Updating is_edited thread fields"""
        for attr, val in validated_data.items():
            if val:
                setattr(instance, attr, val)
        instance.is_edited = True
        instance.save()

        return instance


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for reply"""
    reply = serializers.PrimaryKeyRelatedField(
        queryset=Reply.objects.all(), required=False
    )
    thread = serializers.PrimaryKeyRelatedField(
        queryset=Thread.objects.all(), required=False
    )

    class Meta:
        model = Reply
        fields = [
            'id', 'text', 'image', 'date_created',
            'thread', 'reply', 'is_edited'
        ]
        read_only_fields = ['id', 'is_edited']


class UpvoteSerializer(serializers.ModelSerializer):
    """Serializer for upvote to thread"""
    thread = serializers.PrimaryKeyRelatedField(
        queryset=Thread.objects.all()
    )

    class Meta:
        model = Upvote
        fields = ['id', 'thread']
        read_only_fields = ['id', ]


class DownvoteSerializer(serializers.ModelSerializer):
    """Serializer for upvote to thread"""
    thread = serializers.PrimaryKeyRelatedField(
        queryset=Thread.objects.all()
    )

    class Meta:
        model = Downvote
        fields = ['id', 'thread']
        read_only_fields = ['id', ]
