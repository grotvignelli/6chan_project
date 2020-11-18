from rest_framework import serializers

from core.models import Board, Thread


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
            'date_created', 'board', 'is_edited'
        ]
        read_only_fields = ['id', ]

    def update(self, instance, validated_data):
        """Updating is_edited thread fields"""
        instance.title = validated_data.get('title')
        instance.content = validated_data.get('content')
        instance.image = validated_data.get('image')
        instance.is_edited = True
        instance.save()

        return instance
