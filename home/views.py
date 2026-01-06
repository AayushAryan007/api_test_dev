from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render

def hello(req):     
    return HttpResponse("Hello, welcome to the Home Page!")


def test(req):
    return render(req, "index.html")
