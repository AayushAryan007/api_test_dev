from django.contrib import messages
from django.shortcuts import render,redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# from rest_framework_simplejwt.tokens import RefreshToken

# from .decorators import book_owner_required
from .auth import CookieJWTAuthentication
from .models import Book, BulkUploadTask, AuthToken
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BookSerializer, BulkUploadTaskSerializer
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .tasks import process_book_upload
import csv 
import uuid
from io import StringIO


# @method_decorator(login_required(login_url='login'), name='dispatch')
class BookListCreateAPIView(APIView):
    authentication_classes = []  # Disable DRF auth
    permission_classes = []      # Disable DRF permissions
    
    # get all books 
    def get(self, req):
        if not req.user.is_authenticated:
            if req.headers.get('Accept') == 'application/json':
                return Response({'error': 'Authentication required'}, status=401)
            return redirect('login')  # Or render error page
        
        books = Book.objects.filter(user=req.user)  # Filter by user for security
        serializer = BookSerializer(books, many=True, context={'request': req})
        
        # If API request, return JSON
        if req.headers.get('Accept') == 'application/json':
            return Response(serializer.data)
        
        # Else, render HTML
        context = {"books": serializer.data}
        return render(req, "takebook.html", context)
    
    # create a book
    def post(self, req):
        serializer = BookSerializer(data=req.data, context={'request': req})
        if serializer.is_valid():
            serializer.save(user=req.user)
            return redirect("book-list-create")
        
        # Filter books for context
        books = Book.objects.filter(user=req.user)
        books_ser = BookSerializer(books, many=True, context={'request': req}).data
        return render(req, "takebook.html", {"books": books_ser, "errors": serializer.errors})
        # data = {
        #     'title': req.POST.get('title'),
        #     'author': req.POST.get('author'),
        #     'description': req.POST.get('description'),
        # }

        # serializer = BookSerializer(data = data)
        # if serializer.is_valid():
        #     book = serializer.save(user=req.user)
        #     if req.FILES.get('picture'):
        #         book.picture = req.FILES['picture']
        #         book.save()
        #     # return Response(serializer.data, status=status.HTTP_201_CREATED)
        #     return redirect("book-list-create")
        
        # context = {"books": Book.objects.all(), "errors": serializer.errors}
        # return render(req, "takebook.html", context)
        # # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @method_decorator(login_required(login_url='login'), name='dispatch')
class BookDetailAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    # get, put, delete a book by id
    def get(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user != req.user:
            if req.headers.get('Accept') == 'application/json':
                return Response({'detail': 'Forbidden'}, status=403)
            return render(req, "mybook.html", {"error": "Forbidden"})
        
        serializer = BookSerializer(book, context={'request': req})
        
        # If API request, return JSON
        if req.headers.get('Accept') == 'application/json':
            return Response(serializer.data)
        
        # Else, render HTML
        context = {"book": serializer.data}
        return render(req, "mybook.html", context)
    
    # def put(self, req, id):
    #     book = get_object_or_404(Book, id=id)
    #     serializer = BookSerializer(book, data=req.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         # return Response(serializer.data)
    #         return redirect("book-detail", id=id)
    #     # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # def delete(self, req, id):
    #     book = get_object_or_404(Book, id=id)
    #     book.delete()
    #     # return Response(status=status.HTTP_204_NO_CONTENT)
    #     return redirect("book-list-create")

# @method_decorator(login_required(login_url='login'), name='dispatch')
# @method_decorator(book_owner_required, name='dispatch')
# @book_owner_required
class BookEditAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user != req.user:
            if req.headers.get('Accept') == 'application/json':
                return Response({'detail': 'Forbidden'}, status=403)
            return render(req, "editbook.html", {"error": "Forbidden"})
        
        serializer = BookSerializer(book, context={'request': req})
        
        # If API request, return JSON
        if req.headers.get('Accept') == 'application/json':
            return Response(serializer.data)
        
        # Else, render HTML
        return render(req, "editbook.html", {"book": serializer.data})

    def post(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user != req.user:
            if req.headers.get('Accept') == 'application/json':
                return Response({'detail': 'Forbidden'}, status=403)
            return render(req, "editbook.html", {"book": BookSerializer(book, context={'request': req}).data, "error": "Forbidden"})
        
        serializer = BookSerializer(book, data=req.data, partial=True, context={'request': req})
        if serializer.is_valid():
            serializer.save()
            if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"ok": True})
            return redirect("book-list-create")
        
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": False, "errors": serializer.errors}, status=400)
        
        # Render with errors
        return render(req, "editbook.html", {"book": BookSerializer(book, context={'request': req}).data, "errors": serializer.errors})


class BookDeleteAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user != req.user:
            if req.headers.get('Accept') == 'application/json':
                return Response({'detail': 'Forbidden'}, status=403)
            return JsonResponse({'detail': 'Forbidden'}, status=403)
        
        book.delete()
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": True})
        return redirect("book-list-create")
    


# ///////////////////////////////////////////////////
# User auth apis (functional)
@csrf_exempt
def login_view(req):
    """Login view - CSRF exempt for API usage"""
    if req.method == "POST":
        username = req.POST.get("username")
        password = req.POST.get("password")
        user = authenticate(req, username=username, password=password)
        
        if user is None:
            messages.error(req, "Invalid credentials. Please try again.")
            return render(req, "login.html")
        
        token_obj = AuthToken.create_token(user, expiration_hours=24)

        # For API: return JSON with token
        if req.headers.get('Accept') == 'application/json' or req.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'status': 'success',
                'message': 'Login successful',
                'token': token_obj.token,
                'expires_at': token_obj.expires_at.isoformat(),
                'user_id': user.id,
                'username': user.username,
                'permissions': token_obj.permissions,
            })
        
        
        # refresh = RefreshToken.for_user(user)
        resp = redirect("book-list-create")
        resp.set_cookie('auth_token', token_obj.token, httponly=True, samesite='Strict', secure=False)
        messages.success(req, "Login successful!")
        return resp
        
    return render(req, "login.html")


@csrf_exempt
def signup_view(req):
    """Signup view - CSRF exempt"""
    if req.method == "POST":
        username = req.POST.get("username")
        email = req.POST.get("email")
        password1 = req.POST.get("password1")
        password2 = req.POST.get("password2")

        # Validations
        if password1 != password2:
            messages.error(req, "Passwords do not match")
            return render(req, "register.html")
        
        if User.objects.filter(username=username).exists():
            messages.error(req, "Username already exists")
            return render(req, "register.html")
        
        if User.objects.filter(email=email).exists():
            messages.error(req, "Email already registered")
            return render(req, "register.html")
        
        # create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
         
        # Generate custom auth token
        token_obj = AuthToken.create_token(user, expiration_hours=24)
        

        # For API: return JSON
        if req.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'success',
                'message': 'Signup successful',
                'token': token_obj.token,
                'expires_at': token_obj.expires_at.isoformat(),
                'user_id': user.id,
                'username': user.username,
            }, status=201)
        
        # For web: set cookie and redirect
        resp = redirect("book-list-create")
        resp.set_cookie('auth_token', token_obj.token, httponly=True, samesite='Lax')
        messages.success(req, "Signup successful!")
        return resp



    return render(req, "register.html")
    #return HttpResponse("Signup View - To be implemented")


@csrf_exempt
def logout_view(req):
     # Get token from header or cookie
    token_str = req.META.get('HTTP_AUTHORIZATION', '')[7:] or req.COOKIES.get('auth_token')
    
    if token_str:
        try:
            token_obj = AuthToken.objects.get(token=token_str)
            token_obj.revoke()  # Mark as revoked
        except AuthToken.DoesNotExist:
            pass  # Token already invalid
    
    # Clear cookies (custom token + any old JWT leftovers)
    resp = JsonResponse({'status': 'logged out'})
    resp.delete_cookie('auth_token')  # Your custom token
    resp.delete_cookie('access')      # Old JWT
    resp.delete_cookie('refresh')     # Old JWT
    return resp
# def logout_view(req):
#     logout(req)
#     resp = redirect("login")
#     resp.delete_cookie('access')
#     resp.delete_cookie('refresh')
#     return resp
    #return redirect("login")
    
# ///////////////////////////////////////////////////

# def takebook(request):
#     if request.method == "POST":
#         title = request.POST.get("title")
#         author = request.POST.get("author")
#         description = request.POST.get("description")
#         picture = request.FILES.get("picture")

#         Book.objects.create(
#             title=title,
#             author=author,
#             description=description,
#             picture=picture
#         )
#         print("Book added:", title, author)
#         return redirect("takebook")
    
#     queryset = Book.objects.all()
#     context = {"books": queryset}
#     return render(request, "takebook.html", context)

# def deletebook(req, book_id):
#     book = Book.objects.get(id=book_id)
#     book.delete()
#     return redirect("takebook")

# def mybook(req, id):
#     book = Book.objects.get(id=id)
#     context = {"book": book}
#     return render(req, "mybook.html", context)

# def editbook(req, id):
#     book = Book.objects.get(id=id)
#     if req.method == "POST":
#         book.title = req.POST.get("title")
#         book.author = req.POST.get("author")
#         book.description = req.POST.get("description")
#         if req.FILES.get("picture"):
#             book.picture = req.FILES.get("picture")
#         book.save()
#         return redirect("mybook", id=book.id)
#     context = {"book": book}
#     return render(req, "editbook.html", context)





#HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH


#  bulk upload and bg job views


class BulkUploadBooksAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def _authenticate_token(self, req):
        """Authenticate request using Bearer token in Authorization header."""
        auth_header = req.META.get('HTTP_AUTHORIZATION', '')
        token_str = auth_header[7:] if auth_header.startswith('Bearer ') else None
        print(f"DEBUG bulk-upload auth: header={auth_header}, token_str={token_str}")

        if not token_str:
            return None, Response({'error': 'Missing or invalid Authorization header'}, status=401)

        try:
            token_obj = AuthToken.objects.get(token=token_str)
        except AuthToken.DoesNotExist:
            return None, Response({'error': 'Invalid token'}, status=401)

        if not token_obj.is_valid() or not token_obj.user.is_active:
            return None, Response({'error': 'Token expired or inactive'}, status=401)

        return token_obj.user, None

    def get(self, req):
        user, error_response = self._authenticate_token(req)
        if error_response:
            return error_response
        # Render upload form for authenticated user
        return render(req, "bulk_upload.html", {"user": user})
    
    def post(self, req):
        user, error_response = self._authenticate_token(req)
        if error_response:
            return error_response
        file = req.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)
        # Parse CSV
        file_content = file.read().decode('utf-8')
        reader = csv.DictReader(StringIO(file_content))
        rows = list(reader)
        if not rows:
            return Response({'error': 'CSV is empty'}, status=400)
        batch_id = str(uuid.uuid4())
        valid_rows = 0
        for row in rows:
            title = row.get('title', '').strip()
            author = row.get('author', '').strip()
            description = row.get('description', '').strip()
            # Skip invalid rows
            if not title or not author:
                continue
            
            task = BulkUploadTask.objects.create(
                task_id=uuid.uuid4(),
                batch_id=batch_id,
                title=title,
                author=author,
                description=description,
                status='pending'
            )
            
            # Enqueue task for authenticated user
            celery_task = process_book_upload.delay(str(task.task_id), user.id)
            task.celery_task_id = celery_task.id
            task.save()
            valid_rows += 1
        
        if valid_rows == 0:
            return Response({'error': 'No valid rows in CSV'}, status=400)
        
        return Response({
            'batch_id': batch_id,
            'task_ids': [str(task.task_id) for task in BulkUploadTask.objects.filter(batch_id=batch_id)],
            'total_rows': valid_rows
        }, status=202)
        

class TaskStatusAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = BulkUploadTask.objects.get(task_id=task_id)
            # Optional: Check if task belongs to user (if you add user field to BulkUploadTask)
            serializer = BulkUploadTaskSerializer(task)
            return Response(serializer.data)
        except BulkUploadTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

class BatchStatusAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response({'error': 'batch_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tasks = BulkUploadTask.objects.filter(batch_id=batch_id)
            # Optional: Filter by user if tasks have user field
            
            summary = {
                'batch_id': batch_id,
                'total': tasks.count(),
                'pending': tasks.filter(status='pending').count(),
                'processing': tasks.filter(status='processing').count(),
                'success': tasks.filter(status='success').count(),
                'failed': tasks.filter(status='failed').count(),
                'tasks': BulkUploadTaskSerializer(tasks, many=True).data
            }
            
            return Response(summary)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


