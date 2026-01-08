from django.contrib import messages
from django.shortcuts import render,redirect, get_object_or_404

from rest_framework_simplejwt.tokens import RefreshToken

from .decorators import book_owner_required
from .auth import CookieJWTAuthentication
from .models import Book
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BookSerializer
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


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
class BookEditAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(book_owner_required)
    def get(self, req, id):
        # book = get_object_or_404(Book, id=id)
        book = getattr(self, 'book')
        serializer = BookSerializer(book, context={'request': req})
        context = {"book": serializer.data}
        return render(req, "editbook.html", context)
    
    @method_decorator(book_owner_required)
    def post(self, req, id):
        book = getattr(self, 'book')
        serializer = BookSerializer(book, data=req.data, partial=True, context={'request': req})
        if serializer.is_valid():
            serializer.save()
            # AJAX-friendly
            if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"ok": True})
            return redirect("book-list-create")
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": False, "errors": serializer.errors}, status=400)
        return render(req, "editbook.html", {"book": BookSerializer(book, context={'request': req}).data, "errors": serializer.errors})


# @method_decorator(login_required(login_url='login'), name='dispatch')
# @method_decorator(book_owner_required, name='dispatch')
class BookDeleteAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @method_decorator(book_owner_required)
    def post(self, req, id):
        book = getattr(self, 'book')
        book.delete()
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"ok": True})
        return redirect("book-list-create")
    


# ///////////////////////////////////////////////////
# User auth apis (functional)

def login_view(req):
    if req.method == "POST":
        username= req.POST.get("username")
        password= req.POST.get("password")
        user = authenticate(req, username=username, password=password)
        # if user is not None:
        #     login(req, user)
        #     messages.success(req, "Login successful!")
        #     return redirect("book-list-create")
        # else:
        #     messages.error(req, "Invalid credentials. Please try again.")
        #     return render(req, "login.html")

        if user is None:
            messages.error(req, "Invalid credentials. Please try again.")
            return render(req, "login.html")
        refresh = RefreshToken.for_user(user)
        resp = redirect("book-list-create")
        # set HTTP-only cookies
        resp.set_cookie('access', str(refresh.access_token), httponly=True, samesite='Lax', secure=False)
        resp.set_cookie('refresh', str(refresh), httponly=True, samesite='Lax', secure=False)
        messages.success(req, "Login successful!")
        return resp
        
    return render(req, "login.html")
    #return HttpResponse("Login View - To be implemented")

def signup_view(req):
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