from django.db import models
from django.contrib.auth.models import User
import uuid

import hashlib
from django.utils import timezone
from datetime import timedelta
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
    

# ////////////////////////


# account/models.py

class AuthToken(models.Model):
    """
    Custom authentication token model.
    Token is 64-char string, generated from UUID4 + hash.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    token = models.CharField(max_length=64, unique=True, primary_key=True)  # 64-char token
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()  # Expiration timestamp
    permissions = models.JSONField(default=dict, blank=True)  # Optional: {'scope': 'read', 'permissions': ['book.create']}
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    @staticmethod
    def generate_token():
        """Generate a 64-character token from UUID4 + SHA-256 hash."""
        base_uuid = str(uuid.uuid4())  # 36 chars
        hashed = hashlib.sha256(base_uuid.encode()).hexdigest()[:64]  # 64-char hash
        return hashed
    
    @classmethod
    def create_token(cls, user, expiration_hours=24, permissions=None):
        """Create and save a new token."""
        token_str = cls.generate_token()
        expires_at = timezone.now() + timedelta(hours=expiration_hours)
        permissions = permissions or {}
        
        token_obj = cls.objects.create(
            token=token_str,
            user=user,
            expires_at=expires_at,
            permissions=permissions,
            status='active'
        )
        return token_obj
    
    def is_valid(self):
        """Check if token is valid (active, not expired)."""
        now = timezone.now()
        return (
            self.is_active and
            self.status == 'active' and
            self.expires_at > now
        )
    
    def revoke(self):
        """Revoke the token."""
        self.status = 'revoked'
        self.is_active = False
        self.save()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.user.username} ({self.status})"