from django.db import models

# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    grade = models.CharField(max_length=10)
    classroom = models.CharField(max_length=10)
    number = models.CharField(max_length=15, blank=True, null=True)


    def __str__(self):
        return self.name
    

