from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()
    class Meta:
        model = Book
        # Don't use serializer.data for templates with ImageField
        
        fields = ['id', 'user' ,'title', 'author', 'description','picture',  'picture_url']
        # fields = '__all__'

    def get_picture_url(self, obj):
            if obj.picture:
                request = self.context.get('request')
                return request.build_absolute_uri(obj.picture.url) if request else obj.picture.url
            return None
