from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response #nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User
from meetingserver.models import InviteInfo
from meetingserver.models import ChangedInviteInfo
from meetingserver.models import CreatorAttendanceInfo
from forms.login_form import LoginForm
from forms.new_user_form import NewUserForm

from django.views.decorators.csrf import csrf_protect

def me(request):
    
    if 'user_id' not in request.session:
        return HttpResponseRedirect("/")
    
    # żeby obsługa i GET i POST
    params = request.POST.copy()
    params.update(request.GET)
    
    uname = request.session['user_name']
    myid = request.session['user_id']
    
    new_invite = InviteInfo.objects.filter(user__id=myid)   # ten queryset ma pod .user dostępną krotkę z tabeli user z którą się łączy!!!; ale w filter trzeba __ zamiast .
    new_changed_invite = ChangedInviteInfo.objects.filter(user__id=myid)
    new_attendance = CreatorAttendanceInfo.objects.filter(meeting__creator__id=myid)
    
    return render(request, 'me.html', {'username': uname, 'new_inv': new_invite, 'new_changed': new_changed_invite, \
                                        'new_attendance': new_attendance}) 
    





























    
