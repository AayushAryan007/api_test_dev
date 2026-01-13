"""
URL configuration for proj1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home.views import *
from account.views import *
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
def root(request):
    return HttpResponse("++++++")


urlpatterns = [
    # JWT auth paths
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    # extra
    path('', root, name='root'),
    path('admin/', admin.site.urls),
    path('home/', hello, name='home'),
    path('test/', test, name='test'),
    path('foo/', foo, name='foo'),
    

    # AUTH paths for user
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),



    # book paths
    
    # apiView paths
    path("api/books/", BookListCreateAPIView.as_view(), name="book-list-create"),
    path("api/books/<int:id>/", BookDetailAPIView.as_view(), name="book-detail"),

    
    path('takebook/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('deletebook/<int:id>/', BookDeleteAPIView.as_view(), name='deletebook'),
    path('mybook/<int:id>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('editbook/<int:id>/', BookEditAPIView.as_view(), name='editbook'),

    
    #  functional view paths
    # path('takebook/', takebook, name='takebook'),
    # path('deletebook/<int:book_id>/', deletebook, name='deletebook'),
    # path('mybook/<int:id>/', mybook, name='mybook'),
    # path('editbook/<int:id>/', editbook, name='editbook'),


    # bulk upload endpoints
    path('bulk-upload/', BulkUploadBooksAPIView.as_view(), name='bulk-upload'),
    path('task-status/', TaskStatusAPIView.as_view(), name='task-status'),
    path('batch-status/', BatchStatusAPIView.as_view(), name='batch-status'),

]    

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

