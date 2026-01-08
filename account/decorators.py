from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from .models import Book

def book_owner_required(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        book_id = kwargs.get('id') or kwargs.get('pk')
        book = get_object_or_404(Book, id=book_id)

        if not request.user.is_authenticated:
            # JWT-protected views should return 401 (or redirect for non-AJAX)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'detail': 'Authentication required'}, status=401)
            return redirect('login')

        if book.user_id != request.user.id:
            # AJAX: return 403 for your dropdown alert; non-AJAX: 403 page
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'detail': 'Forbidden'}, status=403)
            return HttpResponseForbidden("Forbidden")

        # Attach to view to avoid re-query
        self.book = book
        return view_func(self, request, *args, **kwargs)
    return _wrapped