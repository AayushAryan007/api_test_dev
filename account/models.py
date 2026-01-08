from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='book_pictures/', blank=True, null=True)
    def __str__(self):
        return self.title