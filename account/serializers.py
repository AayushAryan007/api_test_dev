from rest_framework import serializers
from .models import Book, BulkUploadTask


class BookSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'picture', 'picture_url', 'user']
        read_only_fields = ['id', 'user', 'picture_url']
        extra_kwargs = {
            'author': {'required': True, 'allow_blank': False},
        }
    def get_picture_url(self, obj):
        """Return the picture URL if picture exists"""
        if obj.picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None

    def create(self, validated_data):
        # Get user from context if not in validated_data
        user = self.context.get('user') or self.context.get('request').user if self.context.get('request') else None
        if user:
            validated_data['user'] = user
        return super().create(validated_data)
    
class BulkUploadTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkUploadTask
        fields = ['task_id', 'status', 'title', 'author', 'error_message', 'created_at', 'completed_at']
        read_only_fields = ['task_id', 'status', 'created_at', 'completed_at']
