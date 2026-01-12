from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Book

def book_owner_required(view_class):
    """Decorator for APIView class - checks ownership"""
    original_dispatch = view_class.dispatch
    
    def new_dispatch(self, request, *args, **kwargs):
        book_id = kwargs.get('id')
        if book_id:
            from .models import Book
            from django.shortcuts import get_object_or_404
            book = get_object_or_404(Book, id=book_id)
            
            if not request.user.is_authenticated or book.user_id != request.user.id:
                from django.http import JsonResponse
                return JsonResponse({'detail': 'Forbidden'}, status=403)
            
            self.book = book
        
        return original_dispatch(self, request, *args, **kwargs)
    
    view_class.dispatch = new_dispatch
    return view_class
