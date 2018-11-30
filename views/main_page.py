# !/usr/bin/env/python
# -*- coding: utf-8 -*-
"""
Strony odpowiedzialne za zalogowanie/wylogowanie (ale jeszcze wylogowanie osobno gdzie indziej przy usuwaniu konta)
"""

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response  # nie działa z csrf
from django.shortcuts import render
from django.template import RequestContext
from meetingserver.models import User
from forms.login_form import LoginForm
from forms.new_user_form import NewUserForm
from django import forms

from django.views.decorators.csrf import csrf_protect


@csrf_protect
def get_main_page(request):
    """pokaż stronę główną z formularzem logowania"""
    if 'user_id' in request.session:
        return HttpResponseRedirect("/me")

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # do sprawdzania czy zalogowany
            request.session['user_id'] = form.cleaned_data['id']
            request.session['user_name'] = form.cleaned_data['name']  # login
            return HttpResponseRedirect("/me")
    else:
        form = LoginForm()
    # jak formularz niepoprawny to go też zwraca, bo tam jest wyjęty, i dane
    # są wpisane jakie były!
    return render(request, 'main_page.html', {'form': form})


@csrf_protect
def sign_up(request):
    """ pokaż stronę zakladania nowego konta uzytkownika, z formularzem"""
    if 'user_id' in request.session:
        return HttpResponseRedirect("/me")

    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            # do sprawdzania czy zalogowany
            request.session['user_id'] = form.cleaned_data['id']
            request.session['user_name'] = form.cleaned_data['name']
            return HttpResponseRedirect("/me")
    else:
        form = NewUserForm()
    # jak formularz niepoprawny to go też zwraca, bo tam jest wyjęty, i dane
    # są wpisane jakie były!
    return render(request, 'sign_up.html', {'form': form})


def sign_out(request):
    """ wyloguj"""
    try:
        del request.session['user_id']
        del request.session['name']
        del request.session['ev_us_nr']
    except KeyError:
        pass
    return render(request, 'logged_out.html', {})
