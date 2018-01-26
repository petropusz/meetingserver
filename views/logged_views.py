from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response #nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User, Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import DeletedInfo
from meetingserver.models import CreatorAttendanceInfo
from meetingserver.models import Plan, Perhaps, Invitation, Ignored, Rejected
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
        u1.add((inv.meeting.name, inv.meeting.begin, inv.meeting.end, inv.meeting.creator.name))
        
    u2 = set()
    for inv in new_deleted:
        print ("==="+str(inv.meeting.name)+str( inv.meeting.begin)+str(inv.meeting.end)+str( inv.meeting.creator.name))
        u2.add((inv.meeting.name, inv.meeting.begin, inv.meeting.end, inv.meeting.creator.name))
        
    u3 = set()
    for inv in new_attendance:
        print ("==="+str(inv.meeting.name)+str( inv.meeting.begin)+str(inv.meeting.end)+str( inv.meeting.creator.name))
        u2.add((inv.meeting.name, inv.meeting.begin, inv.meeting.end, inv.attendanceType))
        
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
     
    event_name = None 
    event_id = None   
    if request.method == 'POST':
        print ("'''''''''")
        event_name = request.POST.get('ev_name', '')
    else:
        print ("------------")
        event_name = request.GET.get('ev_name', '')
    
    print ("****" + event_name)
    
    try:
        print ("TRYING TO FIND")
        meeting = Meeting.objects.get(name=event_name)
        print ("FOUND")
        event_id = meeting.id
    except:
        return HttpResponseRedirect("/")
    
    if not event_id:
        return HttpResponseRedirect("/")

    print ("HEH")
    

    #meeting = Meeting.objects.filter(id=event_id)   # ten queryset ma pod .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter trzeba __ zamiast .
    i_plan = Plan.objects.filter(meeting__id = event_id)
    n_plan = set()
    for u in i_plan:
        print ("A")
        n_plan.add(u.user.name)
    i_per = Perhaps.objects.filter(meeting__id = event_id)
    n_per = set()
    for u in i_per:
        print ("B")
        n_per.add(u.user.name)
    i_inv = Invitation.objects.filter(meeting__id = event_id)
    n_inv = set()
    for u in i_inv:
        print ("C")
        n_inv.add(u.user.name)
    i_ign = Ignored.objects.filter(meeting__id = event_id)
    n_ign = set()
    for u in i_ign:
        print ("D")
        n_ign.add(u.user.name)
    i_rej = Rejected.objects.filter(meeting__id = event_id)
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















    
