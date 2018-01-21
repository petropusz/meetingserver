from django.db import models

class User(models.Model):
    name = models.CharField(max_length=50)
    
class Meeting(models.Model):
    name = models.CharField(max_length=50)
    begin = models.DateTimeField()
    end = models.DateTimeField()
    
class Plan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
