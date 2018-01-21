from django.http import HttpResponse
from django.shortcuts import render_to_response #nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User
from forms.login_form import LoginForm
from forms.new_user_form import NewUserForm

from django.views.decorators.csrf import csrf_protect

@csrf_protect
def get_main_page(request):
    # print ("TU JESTEM") 
    #c = {}
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            return HttpResponse("udało się")
    else:
        form = LoginForm()
    #c['form'] = form    
    return render(request, 'main_page.html', {'form': form}) # jak formularz niepoprawny to go też zwraca, bo tam jest wyjęty, i dane są wpisane jakie były!
    
@csrf_protect
def sign_up(request):
    # print ("TU JESTEM") 
    #c = {}
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            return HttpResponse("udało się")
    else:
        form = NewUserForm()
    #c['form'] = form    
    return render(request, 'sign_up.html', {'form': form}) # jak formularz niepoprawny to go też zwraca, bo tam jest wyjęty, i dane są wpisane jakie były!
    
