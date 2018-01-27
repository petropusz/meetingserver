from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response #nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User, Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import DeletedInfo
from meetingserver.models import CreatorAttendanceInfo
from meetingserver.models import Invitation
from forms.login_form import LoginForm
from forms.new_event_form import NewEventForm

from django.views.decorators.csrf import csrf_protect

def get_my_notifications(myid, uname):
    new_invite = InviteInfo.objects.filter(user__id=myid)   # ten queryset ma pod .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter trzeba __ zamiast .
    new_deleted = DeletedInfo.objects.filter(user__id=myid)
    new_attendance = CreatorAttendanceInfo.objects.filter(meeting__creator__id=myid)
    
    u1 = set()
    for inv in new_invite:
        print ("==="+str(inv.meeting.name)+str( inv.meeting.begin)+str(inv.meeting.end)+str( inv.meeting.creator.name))
        u1.add((inv.meeting.id, inv.meeting.name, inv.meeting.begin, inv.meeting.end, inv.meeting.creator.name))
        
    u2 = set()
    for inv in new_deleted:
        #print ("==="+str(inv.meeting.name)+str( inv.meeting.begin)+str(inv.meeting.end)+str( inv.meeting.creator.name))
        u2.add((inv.m_name, inv.m_begin, inv.m_end, inv.m_creator_name))
        
    u3 = set()
    for inv in new_attendance:
        print ("==="+str(inv.meeting.name)+str( inv.meeting.begin)+str(inv.meeting.end)+str( inv.meeting.creator.name))
        u2.add((inv.meeting.id, inv.meeting.name, inv.meeting.begin, inv.meeting.end, inv.attendanceType))
        
    return {'username': uname, 'new_inv': u1, 'new_deleted': u2, \
                                        'new_attendance': u3}

def me(request):
    
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
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr']=1    
        
    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        if form.is_valid():  # nic nie robi (albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę podać parametr a clean chyba nie
                            
            #data = form.cleaned_data
            #request.session['logged'] = True
            form.checkClean(request.session['ev_us_nr'])
            if not form.errors:
                try:
                    print ("starting event creation")
                    print (";;"+str(request.session['user_id']))
                    form.create_event(request.session['user_id'], request.session['ev_us_nr'])
                    del request.session['ev_us_nr']
                    print ("EVENT CREATED, HM")
                except:
                    form.checkClean(request.session['ev_us_nr'])
                    return render(request, 'create_event.html', {'form': form})
                return HttpResponseRedirect("/me") # TODO strona wydarzenia którą zwraca zaakceptowany formularz jako swoje cleaned_data
    else:
        form = NewEventForm() # TODO jak to zrobic żeby było ok
        request.session['ev_us_nr']=1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    #c['form'] = form    
    return render(request, 'create_event.html', {'form': form})
    
def add_user_field(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr']=1    
        
    request.session['ev_us_nr'] += 1    
    print (request.session['ev_us_nr'])
        
    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr']) #add_user()
        
    else:
        form = NewEventForm() 
        request.session['ev_us_nr']=1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    #c['form'] = form    
    return render(request, 'create_event.html', {'form': form})


def delete_user_field(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr']=1    
        
    if request.session['ev_us_nr'] > 1:
        request.session['ev_us_nr'] -= 1   
        
    print (request.session['ev_us_nr'])     
        
    if request.method == 'POST':
        form = NewEventForm(request.POST)
        form.ensure_user_field_nr(request.session['ev_us_nr']) #form.del_user()
        
        # użytkownik może sobie dodawać coś do formularza, jakieś dziwne pola (w html), ale będą ignorowane
    else:
        form = NewEventForm() 
        request.session['ev_us_nr']=1  # jak get, to nowy, więc dajemy 1 
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    #c['form'] = form    
    return render(request, 'create_event.html', {'form': form})



def find_gap_in_plans(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr']=1    
    
    print ("=======" + str(request.session['ev_us_nr']))
        
    if request.method == 'POST':
        form = NewEventForm(request.POST.copy())   # musi być .copy, żeby .data było mutable!!!
        form.ensure_user_field_nr(request.session['ev_us_nr'])   # TO MA ZNACZENIE NA GOTOWYM FORMULARZU, BO FORMULARZ NIBY MA POLA,
                                                                 #  ALE OBIEKT Z KONSTRUKTORA NewEventForm(request.POST) BEZ TEGO ICH NIE MA !!!
        if form.is_valid():  # nic nie robi(albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę podać parametr a clean chyba nie
        # !!  jak użytkownik sobie usunie pola w html'u to się może wywalić,
        #     ale raczej nie chcemy się bawić w sprawdzanie czy sam sobie nie szkodzi
            
            res = form.find_gap_plan(request.session['ev_us_nr'])  # w sumie nieważne jakie res, i tak zwracamy zmieniony formularz (z błędami lub bez)
    else:
        form = NewEventForm() 
        request.session['ev_us_nr']=1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    #c['form'] = form    
    return render(request, 'create_event.html', {'form': form})

def find_gap_in_invs(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    if 'ev_us_nr' not in request.session:
        request.session['ev_us_nr']=1    
        
    if request.method == 'POST':
        form = NewEventForm(request.POST.copy())  # musi być .copy, żeby .data było mutable!!!
        form.ensure_user_field_nr(request.session['ev_us_nr'])
        if form.is_valid():  # nic nie robi(albo może jednak sprawdza format wartości?), potrzebuję żeby mieć cleaned_data wygodnie do modyfikowania w obiekcie formularza
                             # w prawdziwej funkcji walidującej której mogę podać parametr a clean chyba nie
            
            res = form.find_gap_inv(request.session['ev_us_nr'])  # jak zwrócę nowy formularz z wypelnionymi to stracę stare wartości...
    else:
        form = NewEventForm() 
        request.session['ev_us_nr']=1  # jak get, to nowy, więc dajemy 1
        form.ensure_user_field_nr(request.session['ev_us_nr'])
    #c['form'] = form    
    return render(request, 'create_event.html', {'form': form})

    

def show_event(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
     
    print (str(request.GET)) 
     
    event_id = None   
    if request.method == 'POST':
        print ("'''''''''")
        event_id = request.POST.get('ev_id', '')
    else:
        print ("------------")
        event_id = request.GET.get('ev_id', '')
    
    print ("****" + event_id)
    
    try:
        print ("TRYING TO FIND")
        meeting = Meeting.objects.get(id=event_id)
        print ("FOUND")
    except:
        return HttpResponseRedirect("/")
    
    if not event_id:
        return HttpResponseRedirect("/")

    print ("HEH")
    

    #meeting = Meeting.objects.filter(id=event_id)   # ten queryset ma pod .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter trzeba __ zamiast .
    i_plan = Invitation.objects.filter(meeting__id = event_id, reactionType = 1)
    n_plan = set()
    for u in i_plan:
        print ("A")
        n_plan.add(u.user.name)
    i_per = Invitation.objects.filter(meeting__id = event_id, reactionType = 2)
    n_per = set()
    for u in i_per:
        print ("B")
        n_per.add(u.user.name)
    i_inv = Invitation.objects.filter(meeting__id = event_id, reactionType = 3)
    n_inv = set()
    for u in i_inv:
        print ("C")
        n_inv.add(u.user.name)
    i_ign = Invitation.objects.filter(meeting__id = event_id, reactionType = 4)
    n_ign = set()
    for u in i_ign:
        print ("D")
        n_ign.add(u.user.name)
    i_rej = Invitation.objects.filter(meeting__id = event_id, reactionType = 5)
    n_rej = set()
    for u in i_rej:
        print ("E")
        n_rej.add(u.user.name)
    
    print ("CZŁEK:" + meeting.creator.name)
    
    uname = request.session['user_name']
    myid = request.session['user_id']
    
    notif_dict = get_my_notifications(myid, uname)
    
    info = {'meeting_name': meeting.name,
            'meeting_creator': meeting.creator.name, 
            'meeting_begin': meeting.begin, 
            'meeting_end': meeting.end, 
            'meeting_nr_inv': meeting.invitedNr, 
            'meeting_nr_yes': meeting.acceptedNr, 
            'n_plan': n_plan, 
            'n_per': n_per, 
            'n_inv': n_inv, 
            'n_ign': n_ign, 
            'n_rej': n_rej}
    
    return render(request, 'show_event.html', {**info, **notif_dict})




def my_created_events(request): # TODO
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uid = request.session['user_id']

    meeting = Meeting.objects.filter(creator__id=uid)
    
    u1 = set()
    for m in meeting:
        u1.add((m.id, m.name, m.creator.name, m.begin, m.end, m.invitedNr, m.acceptedNr))

    return render(request, 'my_created_events.html', {'my_created_events': u1})

def ask_delete_user(request):

    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")

    uname = request.session['user_name']  # jest wtedy kiedy jest user_id w sesji

    return render(request, 'ask_sure_delete.html', {'name': uname})

"""

def delete_user(request): # TODO

    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
        
    # usuń użytkownika
    
    # trzeba jeszcze zaktualizować wszystkim wydarzeniom na które był zaproszony że maja już o jednego mniej zaproszonego
    # i najlepiej tworzącemu wydarzenie by też dać info że ten usunął konto - numer 6 reakcji będzie na to może
    # JEŚLI TO MA BYĆ W CREATORATTENDANCEINFO TO TRZEBA ZROBIĆ ŻEBY ZAMIAST UŻYTKOWNIKA W KOLUMNIE BYŁA NAZWA - ZMIENIĆ ZNÓW NIECO BAZĘ!!!
    
    # przekieruj na stronę z napisem że usunięto i przyciskiem wróć na główną


def delete_event(request): # TODO
    
    # sprawdź sesję
    
    # sprawdź czy to wydarzenie tego użytkownika

    # dodaj wszystkim którzy byli zaproszeni info o usunięciu do deleted info
    # TODO TRZEBA OCZYWIŚCIE ZMIENIĆ TĘ TABELĘ Z DELETED INFO ŻEBY KOPIOWAŁA POLA WYDARZENIA BO GO JUŻ NIE BĘDZIE
    
    # dopiero na końcu usuń wydarzenie, co spowoduje cascade   
    
def change_reaction(request): #TODO 
    
    # TODO zmienić żeby była jedna tabela zamiast Plan itd., wyszukiwania po Plan np. to teraz będą po tej, ALE
    # Z DODATKOWYM WARUNKIEM coś w stylu reaction.type = 1   (Reactions.filter(type=1, user=...?))
    
    # tu też trzeba ogarnąć zliczanie w wydarzeniu tych, którzy się zgodzili
    
    # TODO jeszcze w odpowiednich miejsach wyświetlać przyciski do zmieniania reakcji
   
"""

    
