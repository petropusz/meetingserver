from django.db import models

class User(models.Model):
    name = models.CharField(max_length=50, unique=True)
    pwd = models.CharField(max_length=50)
    
class Meeting(models.Model):
    name = models.CharField(max_length=50) 
    #nazwy wydarzeń nie muszą być unikalne, ktoś może zaproponować nawet dwa dokładnie takie same, bo czemu nie?
    # ogarniemy które bo klucz zewnętrzny w plan itp.
    begin = models.DateTimeField()
    end = models.DateTimeField()
    invitedNr = models.PositiveIntegerField()
    acceptedNr = models.PositiveIntegerField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    
class Invitation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    reactionType = models.IntegerField() 
    
class InviteInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)

class DeletedInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)
    m_name = models.CharField(max_length=50) 
    m_begin = models.DateTimeField()
    m_end = models.DateTimeField()
    m_invitedNr = models.PositiveIntegerField()
    m_acceptedNr = models.PositiveIntegerField()
    m_creator_name = models.CharField(max_length=50)  # chcemy żeby info o usunięciu zostało po usunięciu użytkownika który tworzył wydarzenie
    #models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'user' )  # nie wie po czym się ma odnieść do usera czy coś

class CreatorAttendanceInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)
    attendanceType = models.IntegerField()










