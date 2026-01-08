from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'user', 'title', 'author', 'description', 'picture', 'picture_url']
        read_only_fields = ['user', 'picture_url']

    def get_picture_url(self, obj):
        if obj.picture:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.picture.url) if request else obj.picture.url
        return None
