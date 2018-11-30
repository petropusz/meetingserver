# !/usr/bin/env/python
# -*- coding: utf-8 -*-

"""formularz tworzenia nowego wydarzenia, do którego użytkownik może sobie dodawać
pola na zaproszonych użytkowników tak, że nie czyści mu wpisanych danych;
może też nakazać znalezienie pierwszego terminu:
- kiedy zaproszeni użytkownicy nie są zaproszeni na żadne inne wydarzenie,
  nie licząc takich, na które odpowiedzieli że
  "nie wiedzą czy wezmą udział", albo że "nie wezmą udziału"
- kiedy zaproszeni użytkownicy nie zadeklarowali się że uczestniczą w
  żadnym innym wydarzeniu"""

from django import forms
from meetingserver.models import User
from meetingserver.models import Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import Invitation
from django.db import transaction
from datetime import datetime
from datetime import timedelta
import pytz  # żeby mieć "timezone-aware" now
from django.utils.dateparse import parse_duration
import copy


def find_first_gap(gap, tab):
    sum = 0
    for i in range(0, len(tab)):
        a, b = tab[i]
        sum += b
        if sum == 0 and i + 1 < len(tab):  # szukamy luki, a nie na końcu
            a2, b2 = tab[i + 1]
            if a2 - gap >= a:
                return a
    a, b = tab[len(tab) - 1]
    return a  # kiedy ostatniemu się ostatnie kończy, skoro nie znaleźliśmy luki


class NewEventForm(forms.Form):

    gapLength = forms.DurationField(
        label="długość przedziału czasu",
        required=False)
    name = forms.CharField(label="nazwa", max_length=50, required=False)
    begin = forms.DateTimeField(label="początek", required=False)
    end = forms.DateTimeField(label="koniec", required=False)
    u1 = forms.CharField(label="użytkownik 1", max_length=50, required=False)
    userFieldNr = forms.CharField(widget=forms.HiddenInput(), initial=1)

    def ensure_user_field_nr(self, uNr):
        """zapewnij odpowiednią liczbę pól na zaproszonych użytkowników"""
        for i in range(1, uNr + 1):
            key = 'u' + str(i)
            if key not in self.fields:
                self.fields[key] = forms.CharField(
                    label="użytkownik " + str(i), max_length=50, required=False)
            else:
                pass

    def getUnames(self, uNr):
        """weź nazwy zaproszony użytkowników"""
        u = set()
        for i in range(1, uNr + 1):
            u.add(self.cleaned_data['u' + str(i)].strip())
        return u

    def find_gap_plan(self, uNr):
        """znajdź pierwszy wolny termin że nie powiedzieli że uczestniczą"""
        gap = parse_duration(self.data['gapLength'])
        self.checkNames(uNr)
        if not gap:
            self.add_error('gapLength', 'Nie podano długości przedziału:')
        if self.errors:
            return False
        unames = self.getUnames(uNr)
        planned = Invitation.objects.filter(
            user__name__in=unames, reactionType=1)
        # czas kompa, może być inny niby niż czas bazy, ale zał. że jest ok;
        # żeby znalazł teraz jeśli się uda
        tab = [(datetime.now(pytz.utc), 0)]
        for p in planned:
            p_begin = p.meeting.begin
            p_end = p.meeting.end
            tab.append((p_begin, +1))
            tab.append((p_end, -1))
        gap_begin = find_first_gap(gap, sorted(tab))
        self.data['begin'] = gap_begin
        self.data['end'] = gap_begin + gap
        return True

    def find_gap_inv(self, uNr):
        """znajdż pierwszy wolny termin że mogą tam mieć tylko 'nie wiem' albo 'nie wezmę udziału'"""
        gap = parse_duration(self.data['gapLength'])
        self.checkNames(uNr)
        if not gap:
            self.add_error('gapLength', 'Nie podano długości przedziału:')
        if self.errors:
            return False
        unames = self.getUnames(uNr)
        possibly_want = set()
        possibly_want.add(1)
        possibly_want.add(2)
        possibly_want.add(3)
        invitations = Invitation.objects.filter(
            user__name__in=unames,
            reactionType__in=possibly_want)  # wszystkie co raczej chcą
        # czas kompa, może być inny niby niż czas bazy, ale zał. że jest ok;
        # żeby znalazł teraz jeśli się uda
        tab = [(datetime.now(pytz.utc), 0)]
        for p in invitations:
            p_begin = p.meeting.begin
            p_end = p.meeting.end
            tab.append((p_begin, +1))
            tab.append((p_end, -1))

        gap_begin = find_first_gap(gap, sorted(tab))
        self.data['begin'] = gap_begin
        self.data['end'] = gap_begin + gap
        return True  # newform

    @transaction.atomic
    # każde żądanie jest transakcją, dekorator został z kiedy tylko to było
    def create_event(self, myuId, uNr):
        """dodaj potrzebne rekordy w bazie danych - utwórz wydarzenie"""
        # to nie może łapać wyjątku w środku jak z dekoratorem, musi być łapany na zewnątrz
        name1 = self.cleaned_data['name']
        begin1 = self.cleaned_data['begin']
        end1 = self.cleaned_data['end']
        myu = User.objects.get(id=myuId)
        # zakładam że twórca wydarzenia niekoniecznie musi na nie iść, i traktuję go jako każdego innego
        # w szczególności może go w ogóle nie być w uczestnikach
        meet = Meeting.objects.create(
            name=name1,
            begin=begin1,
            end=end1,
            invitedNr=uNr,
            acceptedNr=0,
            creator=myu)
        for i in range(1, uNr + 1):
            uname = self.cleaned_data['u' + str(i)].strip()
            u = User.objects.get(name=uname)  # name to klucz, więc możemy tak
            InviteInfo.objects.create(user=u, meeting=meet)
            # 3 to że jeszcze nie zareagował
            Invitation.objects.create(user=u, meeting=meet, reactionType=3)

    def checkNames(self, uNr):
        """sprawdź czy podane nazwy użytkowników są ok"""
        d = set()
        for i in range(1, uNr + 1):
            if 'u' + str(i) in self.cleaned_data:
                uname = self.cleaned_data['u' + str(i)].strip()
                self.cleaned_data['u' + str(i)] = uname
                if uname in d:
                    self.add_error(
                        'u' + str(i), 'Nazwa użytkownika się powtarza:')
                else:
                    try:
                        # name to klucz, więc możemy tak
                        User.objects.get(name=uname)
                    except BaseException:
                        self.add_error(
                            'u' + str(i), 'Użytkownik nie istnieje:')
                if uname:
                    d.add(uname)
            else:
                self.add_error('u' + str(i), 'Nie podano użytkownika:')

    def checkClean(self, uNr):
        """funkcja sprawdzająca czy formularz ma poprawne dane, elastyczniejsza
        od zwykłego clean, bo może mieć dodatkowy argument; dodaje błędy przy polach"""

        self.checkNames(uNr)

        if 'begin' in self.cleaned_data:
            b = self.cleaned_data['begin']
            if not b:
                self.add_error('begin', 'Brak podanego czasu rozpoczęcia:')

        if 'end' in self.cleaned_data:
            b = self.cleaned_data['end']
            if not b:
                self.add_error('end', 'Brak podanego czasu zakończenia:')

        if 'name' in self.cleaned_data:
            n = self.cleaned_data['name'].strip()
            self.cleaned_data['name'] = n
            if not n:
                self.add_error(
                    'name', 'Nazwa wydarzenia zawiera same białe znaki')
        else:
            self.add_error('name', 'Brakuje nazwy')

    def clean(self):
        """nadpisana funkcja sprawdzająca dane formularza, żeby można było np. sobie
        dodać pole na użytkownika kiedy dane jeszcze nie są poprawne (wysyłając formularz,
        i dostając zmodyfikowany z polem, ale bez wymazanych danych z powrotem)"""

        # tu nic nie robimy, żeby można było robić submit bez sprawdzania!
