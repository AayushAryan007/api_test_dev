from django.contrib import messages
from django.shortcuts import render,redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken

# from .decorators import book_owner_required
from .auth import CookieJWTAuthentication
from .models import Book, BulkUploadTask
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
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    # get all books 
    def get(self, req):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True, context={'request': req})
        # return Response(serializer.data)
        context = {"books": serializer.data}
        return render(req, "takebook.html", context)
    
    # create a book
    def post(self, req):
        # Use req.data (handles multipart/form-data including files)
        serializer = BookSerializer(data=req.data, context={'request': req})
        if serializer.is_valid():
            # Ensure owner is set
            serializer.save(user=req.user)
            return redirect("book-list-create")
        print("Serializer errors:", serializer.errors)

        # Keep context type consistent: always pass serializer.data
        books = Book.objects.all()
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
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    # get, put, delete a book by id
    def get(self, req, id):
        book = get_object_or_404(Book, id=id)
        serializer = BookSerializer(book)
        context = {"book": serializer.data}
        return render(req, "mybook.html", context)
        # return Response(serializer.data)
    
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
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user_id != req.user.id:
            return JsonResponse({'detail': 'Forbidden'}, status=403)
        
        serializer = BookSerializer(book, context={'request': req})
        return render(req, "editbook.html", {"book": serializer.data})

    def post(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user_id != req.user.id:
            return JsonResponse({'detail': 'Forbidden'}, status=403)
        
        serializer = BookSerializer(book, data=req.data, partial=True, context={'request': req})
        if serializer.is_valid():
            serializer.save()
            if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"ok": True})
            return redirect("book-list-create")
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": False, "errors": serializer.errors}, status=400)
        return render(req, "editbook.html", {"book": BookSerializer(book, context={'request': req}).data, "errors": serializer.errors})


class BookDeleteAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, req, id):
        book = get_object_or_404(Book, id=id)
        # Check ownership
        if book.user_id != req.user.id:
            return JsonResponse({'detail': 'Forbidden'}, status=403)
        
        book.delete()
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": True})
        return redirect("book-list-create")
    


# ///////////////////////////////////////////////////
# User auth apis (functional)
# @csrf_exempt
def login_view(req):
    """Login view - CSRF exempt for API usage"""
    if req.method == "POST":
        username = req.POST.get("username")
        password = req.POST.get("password")
        user = authenticate(req, username=username, password=password)
        
        if user is None:
            messages.error(req, "Invalid credentials. Please try again.")
            return render(req, "login.html")
        
        refresh = RefreshToken.for_user(user)
        resp = redirect("book-list-create")
        resp.set_cookie('access', str(refresh.access_token), httponly=True, samesite='Lax', secure=False)
        resp.set_cookie('refresh', str(refresh), httponly=True, samesite='Lax', secure=False)
        messages.success(req, "Login successful!")
        return resp
        
    return render(req, "login.html")



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
         
        messages.success(req, "Account created successfully! Please login.")
        return redirect("login")



    return render(req, "register.html")
    #return HttpResponse("Signup View - To be implemented")


def logout_view(req):
    logout(req)
    resp = redirect("login")
    resp.delete_cookie('access')
    resp.delete_cookie('refresh')
    return resp
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
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, req):
        file = req.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_content = file.read().decode('utf-8').strip()  # Strip whitespace
        # print(f"File content:\n{repr(file_content)}")  
        
        # Split by newline manually to debug
        lines = file_content.split('\n')
        print(f"Total lines: {len(lines)}")
        for i, line in enumerate(lines):
            print(f"Line {i}: {repr(line)}")
    
        reader = csv.DictReader(StringIO(file_content))
        rows_list = list(reader)
        # print(f"Total rows parsed: {len(rows_list)}")
    
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        for row in rows_list:
            print(f"Processing row: {row}")
            task = BulkUploadTask.objects.create(
                task_id=uuid.uuid4(),
                batch_id=batch_id,
                title=row.get('title'),
                author=row.get('author'),
                description=row.get('description', ''),
                status='pending'
                # Remove: user=req.user
            )
            celery_task = process_book_upload.delay(str(task.task_id), req.user.id)
            task.celery_task_id = celery_task.id
            task.save()
            task_ids.append(str(task.task_id))
        
        return Response({
            'batch_id': batch_id,
            'task_ids': task_ids,
            'total_rows': len(task_ids)
        }, status=status.HTTP_202_ACCEPTED)
        

class TaskStatusAPIView(APIView):
    """
    GET: Check status of a single task
    ?task_id=<uuid>
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = BulkUploadTask.objects.get(task_id=task_id)
            serializer = BulkUploadTaskSerializer(task)
            return Response(serializer.data)
        except BulkUploadTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
       

class BatchStatusAPIView(APIView):
    """
    GET: Check status of all tasks in a batch
    ?batch_id=<uuid>
    """

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response({'error': 'batch_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tasks = BulkUploadTask.objects.filter(batch_id=batch_id)
            
            # Summary stats
            summary = {
                'batch_id': batch_id,
                'total': tasks.count(),
                'pending': tasks.filter(status='pending').count(),
                'processing': tasks.filter(status='processing').count(),
                'success': tasks.filter(status='completed').count(),
                'failed': tasks.filter(status='failed').count(),
                'tasks': BulkUploadTaskSerializer(tasks, many=True).data
            }
            
            return Response(summary)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


