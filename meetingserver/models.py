# !/usr/bin/env/python
# -*- coding: utf-8 -*-
"""
plik z modelem bazy danych
"""


from django.db import models


class User(models.Model):
    name = models.CharField(max_length=50, unique=True)
    pwd = models.CharField(max_length=50)


class Meeting(
        models.Model):  # znika jak znika użytkownik który je utworzył (bo cascade), albo jak je usunie
    name = models.CharField(max_length=50)
    # nazwy wydarzeń nie muszą być unikalne, ktoś może zaproponować nawet dwa dokładnie takie same, bo czemu nie?
    # ogarniemy które bo klucz zewnętrzny w plan itp.
    begin = models.DateTimeField()
    end = models.DateTimeField()
    invitedNr = models.PositiveIntegerField()
    acceptedNr = models.PositiveIntegerField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)


class Invitation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # zniknie jak wydarzenie zniknie, jak tworzący też
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    reactionType = models.IntegerField()


class InviteInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # zniknie jak wydarzenie zniknie, jak tworzący też
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)


class DeletedInfo(models.Model):
    # użytkownik któremu dajemy info, że wydarzenie na które miał iść zostało
    # usunięte
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)
    m_name = models.CharField(max_length=50)
    m_begin = models.DateTimeField()
    m_end = models.DateTimeField()
    m_invitedNr = models.PositiveIntegerField()
    m_acceptedNr = models.PositiveIntegerField()
    # chcemy żeby info o usunięciu zostało po usunięciu użytkownika który
    # tworzył wydarzenie
    m_creator_name = models.CharField(max_length=50)
    # models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'user'
    # )  # nie wie po czym się ma odnieść do usera czy coś


class CreatorAttendanceInfo(
        models.Model):  # info o reakcjach użytkowników którzy jeszcze istnieją; jak usuną konto to to zniknie, a info że usunęli będzie
                                            # w tabeli
                                            # DeletedUserEventCreatorInfo
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    #time = models.DateTimeField(auto_now=True)
    attendanceType = models.IntegerField()


class DeletedUserEventCreatorInfo(models.Model):
    user_name = models.CharField(max_length=50)
    # zniknie jak zniknie wydarzenie
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
