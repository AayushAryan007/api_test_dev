from django.db import models
from django.contrib.auth.models import User
import uuid
# Create your models here.


class Book(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.CharField(max_length=100,null=False, blank=False)
    picture = models.ImageField(upload_to='book_pictures/', blank=True, null=True)
    def __str__(self):
        return self.title
    

class BulkUploadTask(models.Model):
    """Track Status of each csv row upload"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    #csv row data
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)


    #status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    created_book_id = models.ForeignKey(Book, on_delete=models.SET_NULL, blank=True, null=True)

    #Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    #bulk upload batch ID (group tasks together)
    batch_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['status']),
        ]
    def __str__(self):
        return f"{self.task_id} - {self.title} ({self.status})"