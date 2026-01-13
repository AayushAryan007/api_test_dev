
import time
from celery import shared_task
from django.utils import timezone
from .models import Book, BulkUploadTask
from .serializers import BookSerializer
from django.contrib.auth.models import User

@shared_task(bind=True, max_retries=3)
def process_book_upload(self, task_id_str, user_id):
    """
    Process a single book upload task.
    task_id_str: UUID string of BulkUploadTask record
    user_id: User ID
    """
    try:
        # Fetch BulkUploadTask record from DB
        task = BulkUploadTask.objects.get(task_id=task_id_str)

        # Mark task as processing
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.save()
        
        time.sleep(0.5)  # simulate delay per entry
        
        user = User.objects.get(id=user_id)
        
        # Use serializer for validation
        serializer = BookSerializer(data={
            'title': task.title,
            'author': task.author,
            'description': task.description or ""
        })
        
        if serializer.is_valid():
            book = serializer.save(user=user)
            
            task.status = 'completed'
            task.result = {'book_id': book.id}
        else:
            # Validation failed
            task.status = 'failed'
            task.error_message = str(serializer.errors)
            task.result = {'errors': serializer.errors}
        
        task.completed_at = timezone.now()
        task.save()
        return task.result
    
    except BulkUploadTask.DoesNotExist:
        return {'error': 'Task not found'}
    
    except Exception as exc:
        try:
            task = BulkUploadTask.objects.get(task_id=task_id_str)
            task.status = 'failed'
            task.error_message = str(exc)
            task.completed_at = timezone.now()
            task.save()
        except:
            pass
        raise self.retry(exc=exc, countdown=5)
    
    
# import time
# from celery import shared_task
# from django.utils import timezone
# from .models import Book, BulkUploadTask
# from django.contrib.auth.models import User

# @shared_task(bind=True, max_retries=3)
# def process_book_upload(self, task_id_str, user_id):
#     """
#     Process a single book upload task.
#     task_id_str: UUID string of BulkUploadTask record
#     user_id: User ID
#     """
#     try:
#         task = BulkUploadTask.objects.get(task_id=task_id_str)
#         task.status = 'processing'
#         task.celery_task_id = self.request.id
#         task.save()
        
#         time.sleep(0.5)  # simulate work
        
#         user = User.objects.get(id=user_id)
        
#         # Create book directly, no serializer
#         book = Book.objects.create(
#             title=task.title,
#             author=task.author,
#             description=task.description or "",
#             user=user
#         )
        
#         task.status = 'completed'
#         task.result = {'book_id': book.id}
#         task.completed_at = timezone.now()
#         task.save()
#         return task.result
    
#     except BulkUploadTask.DoesNotExist:
#         return {'error': 'Task not found'}
    
#     except Exception as exc:
#         try:
#             task = BulkUploadTask.objects.get(task_id=task_id_str)
#             task.status = 'failed'
#             task.error_message = str(exc)
#             task.completed_at = timezone.now()
#             task.save()
#         except:
#             pass
#         raise self.retry(exc=exc, countdown=5)