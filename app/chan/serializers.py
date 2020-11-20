from rest_framework import serializers

from core.models import (
    Board, Thread, Upvote, Downvote
)


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for board model"""

    class Meta:
        model = Board
        fields = ['id', 'name', 'code']
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
            'date_created', 'board',
            'upvote_thread', 'downvote_thread',
            'is_edited'
        ]
        read_only_fields = ['id', 'is_edited', ]

    def update(self, instance, validated_data):
        """Updating is_edited thread fields"""
        instance.title = validated_data.get('title')
        instance.content = validated_data.get('content')
        instance.image = validated_data.get('image')
        instance.is_edited = True
        instance.save()

        return instance


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
