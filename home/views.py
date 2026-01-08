from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render

def hello(req):     
    return HttpResponse("Hello, welcome to the Home Page!")


def test(req):
    return render(req, "index.html")


def foo(req):
    people =[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
        {"name": "Diana", "age": 28},
        { "name": "Eve", "age": 22 }
    ]

    return render(req, "foo.html", {"people": people})