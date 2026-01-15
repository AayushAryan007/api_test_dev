import time
from celery import shared_task
from django.utils import timezone
from .models import Book, BulkUploadTask

@shared_task(bind=True, max_retries=3)
def process_book_upload(self, task_id_str, user_id):
    """
    Async task: process single CSV row with 0.5s delay
    """
    try:
        # Fetch BulkUploadTask record from DB
        task = BulkUploadTask.objects.get(task_id=task_id_str)
        
        # Validate user_id
        if not user_id:
            raise ValueError("user_id is required")
        
        # Validate title and author
        if not task.title or not task.author:
            raise ValueError("Title and author are required")
        
        # Mark as processing
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.save()
        
        # Simulate 0.5s delay per entry
        time.sleep(0.5)
        
        # Create Book in DB
        book = Book.objects.create(
            title=task.title,
            author=task.author,
            description=task.description or "",
            user_id=user_id
        )
        
        # Mark as success
        task.status = 'success'
        task.created_book_id = book
        task.completed_at = timezone.now()
        task.save()
        
        return {'task_id': str(task.task_id), 'status': 'success', 'book_id': book.id}
    
    except BulkUploadTask.DoesNotExist:
        return {'error': 'Task record not found'}
    
    except Exception as exc:
        # Mark task as failed and return (do not retry) so the batch API always shows the task
        try:
            task = BulkUploadTask.objects.get(task_id=task_id_str)
            task.status = 'failed'
            task.error_message = str(exc)
            task.completed_at = timezone.now()
            task.save()
        except BulkUploadTask.DoesNotExist:
            pass

        return {'task_id': task_id_str, 'status': 'failed', 'error': str(exc)}