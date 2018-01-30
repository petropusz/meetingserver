# !/usr/bin/env/python
# -*- coding: utf-8 -*-
"""główny duży moduł z funkcjami obsługującymi po zalogowaniu;
każde żądanie powinien obsługiwac oddzielny wątek;
każde żądanie ma atomiczną transakcję w bazie (patrz plik settings)"""

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response  # nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User, Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import DeletedInfo
from meetingserver.models import CreatorAttendanceInfo, DeletedUserEventCreatorInfo
from meetingserver.models import Invitation
from forms.login_form import LoginForm
from forms.new_event_form import NewEventForm

from django.views.decorators.csrf import csrf_protect


def get_my_notifications(myid, uname):
    """wydostań z bazy moje powiadomienia"""
    new_invite = InviteInfo.objects.filter(
        user__id=myid)   # ten queryset ma pod .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter trzeba __ zamiast .
    new_deleted = DeletedInfo.objects.filter(user__id=myid)
    new_attendance = CreatorAttendanceInfo.objects.filter(
        meeting__creator__id=myid)
    deleted_attending_users_info = DeletedUserEventCreatorInfo.objects.filter(
        meeting__creator__id=myid)

    u1 = set()
    for inv in new_invite:
        u1.add(
            (inv.meeting.id,
             inv.meeting.name,
             inv.meeting.begin,
             inv.meeting.end,
             inv.meeting.creator.name))

    u2 = set()
    for inv in new_deleted:
        u2.add((inv.id, inv.m_name, inv.m_begin, inv.m_end, inv.m_creator_name))

    u3 = set()
    for inv in new_attendance:
        u3.add(
            (inv.id,
             inv.user.name,
             inv.meeting.id,
             inv.meeting.name,
             inv.meeting.begin,
             inv.meeting.end,
             inv.attendanceType))
    for inv in deleted_attending_users_info:
        u3.add(
            (inv.id,
             inv.user_name,
             inv.meeting.id,
             inv.meeting.name,
             inv.meeting.begin,
             inv.meeting.end,
             6))  # żeby było w 1 zbiorze

    return {'username': uname, 'new_inv': u1, 'new_deleted': u2,
            'new_attendance': u3}


def me(request):
    """wyświetl stronę główną po zalogowaniu, tylko pasek nawig., nazwa użytkownika i powiadomienia"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    # żeby obsługa i GET i POST
    params = request.POST.copy()
    params.update(request.GET)

    uname = request.session['user_name']
    myid = request.session['user_id']

    notif_dict = get_my_notifications(myid, uname)

    return render(request, 'me.html', notif_dict)


def create_event(request):
    """obsługa polecenia tworzenia wydarzenia przez formularz tworzenia wydarzenia"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr'] = 1

    uid = request.session['user_id']
    uname = request.session['user_name']

    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        if form.is_valid():  # nic nie robi (albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę
                             # podać parametr a clean chyba nie

            form.checkClean(request.session['ev_us_nr'])
            if not form.errors:
                try:
                    form.create_event(
                        request.session['user_id'],
                        request.session['ev_us_nr'])
                    del request.session['ev_us_nr']

                except BaseException:
                    form.checkClean(request.session['ev_us_nr'])
                    return render(request, 'create_event.html', {'form': form})
                # TODO strona wydarzenia którą zwraca zaakceptowany formularz
                # jako swoje cleaned_data
                return HttpResponseRedirect("/me")
    else:
        form = NewEventForm()
        request.session['ev_us_nr'] = 1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    notif_dict = get_my_notifications(uid, uname)
    d1 = {'form': form}
    return render(request, 'create_event.html', {**notif_dict, **d1})


def add_user_field(request):
    """obsługa polecenia dodania pola na zaproszonego użytkownika w formularzu
    tworzenia wydarzenia"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr'] = 1

    request.session['ev_us_nr'] += 1

    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr'])  # add_user()

    else:
        form = NewEventForm()
        request.session['ev_us_nr'] = 1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    return render(request, 'create_event.html', {'form': form})


def delete_user_field(request):
    """obsługa polecenia usunięcia pola na zaproszonego użytkownika w formularzu
    tworzenia wydarzenia"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr'] = 1

    if request.session['ev_us_nr'] > 1:
        request.session['ev_us_nr'] -= 1

    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        # użytkownik może sobie dodawać coś do formularza, jakieś dziwne pola
        # (w html), ale będą ignorowane
    else:
        form = NewEventForm()
        request.session['ev_us_nr'] = 1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    return render(request, 'create_event.html', {'form': form})


def find_gap_in_plans(request):
    """znajdź pierwszą dostatecznie długą lukę że zaproszeni nie powiedzieli
    że będą na jakimś spotkaniu w trakcie"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr'] = 1

    if request.method == 'POST':
        # musi być .copy, żeby .data było mutable!!!
        form = NewEventForm(request.POST.copy())
        # TO MA ZNACZENIE NA GOTOWYM FORMULARZU, BO FORMULARZ NIBY MA POLA,
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        # ALE OBIEKT Z KONSTRUKTORA NewEventForm(request.POST) BEZ TEGO ICH NIE
        # MA !!!
        if form.is_valid():  # nic nie robi(albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę podać parametr a clean chyba nie
            # !!  jak użytkownik sobie usunie pola w html'u to się może wywalić,
            # ale raczej nie chcemy się bawić w sprawdzanie czy sam sobie nie
            # szkodzi

            # w sumie nieważne jakie res, i tak zwracamy zmieniony formularz (z
            # błędami lub bez)
            res = form.find_gap_plan(request.session['ev_us_nr'])
    else:
        form = NewEventForm()
        request.session['ev_us_nr'] = 1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    return render(request, 'create_event.html', {'form': form})


def find_gap_in_invs(request):
    """znajdź pierwszą lukę gdzie nie mogą mieć zaproszeń, chyba że powiedzieli
    że nie wiedzą czy będą albo że ich nie będzie"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr'] = 1

    if request.method == 'POST':
        # musi być .copy, żeby .data było mutable!!!
        form = NewEventForm(request.POST.copy())
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        if form.is_valid():  # nic nie robi(albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę
                             # podać parametr a clean chyba nie

            # jak zwrócę nowy formularz z wypelnionymi to stracę stare
            # wartości...
            res = form.find_gap_inv(request.session['ev_us_nr'])
    else:
        form = NewEventForm()
        request.session['ev_us_nr'] = 1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    return render(request, 'create_event.html', {'form': form})


def show_event(request):
    """wyświetl wydarzenie z początkiem, końcem, zaproszonymi i jak zareagowali na zaproszenie,
    - jeśli ten użytkownik je utworzył, to wyświetl mu przycisk do usunięcia
    - jeśli ten użytkownik jest zaproszony, to wyświetl mu przyciski reakcji"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    print(str(request.GET))

    event_id = None
    if request.method == 'POST':
        event_id = request.POST.get('ev_id', '')
    else:
        event_id = request.GET.get('ev_id', '')

    try:
        meeting = Meeting.objects.get(id=event_id)

    except BaseException:
        return HttpResponseRedirect("/")

    if not event_id:
        return HttpResponseRedirect("/")

    # można by też w osobnej funkcji tylko jak wyświetlanie z powiadomień,
    # ale tak wygodniej, a nie jest aż takie nieefektywne
    uid = request.session['user_id']
    notif = InviteInfo.objects.filter(user__id=uid, meeting_id=meeting.id)
    notif.delete()

    # meeting = Meeting.objects.filter(id=event_id)   # ten queryset ma pod
    # .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter
    # trzeba __ zamiast .
    i_plan = Invitation.objects.filter(meeting__id=event_id, reactionType=1)
    n_plan = set()
    for u in i_plan:
        n_plan.add(u.user.name)
    i_per = Invitation.objects.filter(meeting__id=event_id, reactionType=2)
    n_per = set()
    for u in i_per:
        n_per.add(u.user.name)
    i_inv = Invitation.objects.filter(meeting__id=event_id, reactionType=3)
    n_inv = set()
    for u in i_inv:
        n_inv.add(u.user.name)
    i_ign = Invitation.objects.filter(meeting__id=event_id, reactionType=4)
    n_ign = set()
    for u in i_ign:
        n_ign.add(u.user.name)
    i_rej = Invitation.objects.filter(meeting__id=event_id, reactionType=5)
    n_rej = set()
    for u in i_rej:
        n_rej.add(u.user.name)

    uname = request.session['user_name']
    myid = request.session['user_id']

    my_event = (meeting.creator.id == myid)

    notif_dict = get_my_notifications(myid, uname)

    my_inv_reac = -1
    try:
        reaction = Invitation.objects.get(user__id=myid, meeting__id=event_id)
        my_inv_reac = reaction.reactionType
    except BaseException:
        pass

    info = {
        'meeting_name': meeting.name,
        'meeting_creator': meeting.creator.name,
        'meeting_begin': meeting.begin,
        'meeting_end': meeting.end,
        'meeting_nr_inv': meeting.invitedNr,
        'meeting_nr_yes': meeting.acceptedNr,
        'n_plan': n_plan,
        'n_per': n_per,
        'n_inv': n_inv,
        'n_ign': n_ign,
        'n_rej': n_rej,
        'my_event': my_event,
        'm_id': meeting.id,
        'my_invited_reaction': my_inv_reac,
        'list_1245': [
            1,
            2,
            4,
            5]}  # list_1245 muszę przekazywać bo szablony django w html tego nie obsługują

    return render(request, 'show_event.html', {**info, **notif_dict})


def my_created_events(request):
    """wyświetl wydarzenia utworzone przez tego użytkownika, tzn listę,
    z przyciskami którymi można wyświetlać szczegóły"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']
    uname = request.session['user_name']

    meeting = Meeting.objects.filter(creator__id=uid)

    u1 = set()
    for m in meeting:
        u1.add(
            (m.id,
             m.name,
             m.creator.name,
             m.begin,
             m.end,
             m.invitedNr,
             m.acceptedNr))

    notif_dict = get_my_notifications(uid, uname)
    d1 = {'my_created_events': u1}

    return render(request, 'my_created_events.html', {**d1, **notif_dict})


def ask_delete_user(request):
    """spytaj czy użytkownik na pewno chce usunąć konto"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    # jest wtedy kiedy jest user_id w sesji
    uname = request.session['user_name']

    return render(request, 'ask_sure_delete.html', {'name': uname})


def ok_deleted_att_event_info(request):
    """kliknij info że wydarzenie co był zaproszony usunięte,
    żeby się już powiadomienie nie wyświetlało"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    row_id = None
    if request.method == 'POST':
        row_id = request.POST.get('row_id', '')
    else:
        row_id = request.GET.get('row_id', '')

    info = DeletedInfo.objects.get(id=row_id)

    info.delete()

    # daję na główną żeby się już nie bawić w ogarnianie gdzie był
    return HttpResponseRedirect("/me")


def delete_user(request):  # TODO
    """usuń użytkownika"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    thisUsr = User.objects.get(id=uid)
    uname = thisUsr.name

    # chcemy zaktualizować info wydarzeniom na które był zaproszony
    invited = Invitation.objects.filter(user__id=uid)
    meetings_invited = set()
    for inv in invited:
        meetings_invited.add((inv.meeting, inv.reactionType))
    for meeting, reac in meetings_invited:
        meeting.invitedNr -= 1
        if reac == 1:
            meeting.acceptedNr -= 1
        meeting.save()
        DeletedUserEventCreatorInfo.objects.create(
            user_name=uname, meeting=meeting)
        # chcemy dać info twórcom wydarzeń w których uczestniczy że usunął

    # chcemy dać uczestnikom jego wydarzeń info że usunięte
    meetings_created = Meeting.objects.filter(creator__id=uid)
    for meeting in meetings_created:
        invitationsAttending = Invitation.objects.filter(
            meeting__id=meeting.id)
        for inv in invitationsAttending:
            DeletedInfo.objects.create(
                user=inv.user,
                m_name=meeting.name,
                m_begin=meeting.begin,
                m_end=meeting.end,
                m_invitedNr=meeting.invitedNr,
                m_acceptedNr=meeting.acceptedNr,
                m_creator_name=uname)

    thisUsr.delete()

    # trzeba go wylogować też
    try:
        del request.session['user_id']
        del request.session['name']
        del request.session['ev_us_nr']
    except KeyError:
        pass
    return render(request, 'logged_out.html', {})

    return render(request, 'user_deleted.html', {'name': uname})


def delete_event(request):  # przycisk do usuwania tylko w widoku wydarzenia
    """usuń wydarzenie - dostępne dla twórcy wydarzenia z podglądu wydarzenia"""

    # sprawdź sesję
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    event_id = None
    if request.method == 'POST':
        event_id = request.POST.get('ev_id', '')
    else:
        event_id = request.GET.get('ev_id', '')

    try:
        meeting = Meeting.objects.get(id=event_id)
    except BaseException:
        return HttpResponseRedirect("/")

    if not event_id:
        return HttpResponseRedirect("/")

    # sprawdź czy to wydarzenie tego użytkownika
    if meeting.creator.id != uid:
        return HttpResponseRedirect("/")

    # dodaj wszystkim którzy byli zaproszeni info o usunięciu do deleted info
    invitationsAttending = Invitation.objects.filter(meeting__id=meeting.id)
    for inv in invitationsAttending:
        DeletedInfo.objects.create(
            user=inv.user,
            m_name=meeting.name,
            m_begin=meeting.begin,
            m_end=meeting.end,
            m_invitedNr=meeting.invitedNr,
            m_acceptedNr=meeting.acceptedNr,
            m_creator_name=meeting.creator.name)

    # dopiero na końcu usuń wydarzenie, co spowoduje cascade
    meeting.delete()

    # ew. przekierowywać do adresu pobranego z ukrytego pola formularza -
    # tego, z ktorego przyszło żądanie
    return HttpResponseRedirect("/me")


def my_invitations(request):
    """wyświetl listę wydarzeń na które byłem zaproszony i jak reagowałem"""

    # sprawdź sesję
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']
    uname = request.session['user_name']

    attending = Invitation.objects.filter(user__id=uid)

    u1 = set()
    for m in attending:
        u1.add(
            (m.meeting.id,
             m.meeting.name,
             m.meeting.creator.name,
             m.meeting.begin,
             m.meeting.end,
             m.meeting.invitedNr,
             m.meeting.acceptedNr,
             m.reactionType))

    notif_dict = get_my_notifications(uid, uname)
    d1 = {'my_invited_events': u1}

    return render(request, 'my_invited_events.html', {**d1, **notif_dict})


def ok_attendance_not_del(request):
    """zrób żeby info o reakcji innego użytkownika na zaproszenie które dał ten się nie wyświetlało"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    row_id = None
    if request.method == 'POST':
        row_id = request.POST.get('row_id', '')
    else:
        row_id = request.GET.get('row_id', '')

    # ok, bo inny nie może tego row_id - jak ze strony to się nie wywali
    info = CreatorAttendanceInfo.objects.get(id=row_id)

    info.delete()

    # daję na główną żeby się już nie bawić w ogarnianie gdzie był
    return HttpResponseRedirect("/me")


def ok_attendance_del(request):
    """zrób żeby powiadomienie że użytkownik którego ten zaprosił usunął konto się już nie wyświetlało"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    row_id = None
    if request.method == 'POST':
        row_id = request.POST.get('row_id', '')
    else:
        row_id = request.GET.get('row_id', '')

    # ok, bo inny nie może tego row_id - jak ze strony to się nie wywali
    info = DeletedUserEventCreatorInfo.objects.get(id=row_id)

    info.delete()

    # daję na główną żeby się już nie bawić w ogarnianie gdzie był
    return HttpResponseRedirect("/me")


# reakcje tylko z poziomu wyświetlonego zdarzenia
def change_reaction(request):
    """zmień reakcję tego użytkownika na dane zaproszenie"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    reac = None
    ev_id = None
    if request.method == 'POST':
        reac = int(request.POST.get('new_reaction', ''))
        ev_id = request.POST.get('ev_id', '')
    else:
        reac = int(request.GET.get('new_reaction', ''))
        ev_id = request.GET.get('ev_id', '')

    try:
        # na filter potem było źle, bo .coś, a except pięknie łapało...
        meeting = Meeting.objects.get(id=ev_id)
        # na filter potem było źle, bo .coś, a except pięknie łapało...
        reaction = Invitation.objects.get(user__id=uid, meeting__id=ev_id)
        if reac == 1:  # nowa reakcja; najpierw zwiększanie, żeby nie spadło poniżej zera, bo PositiveIntegerField
            meeting.acceptedNr = meeting.acceptedNr + 1
        meeting.save()
        if reaction.reactionType == 1:  # stara reakcja
            meeting.acceptedNr = meeting.acceptedNr - 1
        meeting.save()
        reaction.reactionType = reac
        reaction.save()
    except BaseException:
        HttpResponseRedirect("/me")

    return HttpResponseRedirect("/me")


def show_users(request):
    """wyświetl listę wszystkich użytkowników"""
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']
    uname = request.session['user_name']

    usrs = User.objects.all()

    u1 = set()
    for u in usrs:
        u1.add((u.name))

    notif_dict = get_my_notifications(uid, uname)
    d1 = {'usrs': u1}

    return render(request, 'all_users.html', {**notif_dict, **d1})
