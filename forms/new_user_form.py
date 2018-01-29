# !/usr/bin/env/python
# -*- coding: utf-8 -*-
"""formularz tworzenia nowego konta"""

from django import forms
from meetingserver.models import User

class NewUserForm(forms.Form):
    name = forms.CharField(label="login", max_length=50)
    pwd = forms.CharField(label="hasło", max_length=50, widget=forms.PasswordInput)
    pwdEnsure =  forms.CharField(label = "powtórz hasło", max_length=50, widget=forms.PasswordInput)
    
    #najpierw są uruchamiane clean_field, a potem clean; można też nie robić clean_field żeby nie trzeba spr form.errors
    
    #nic nie robi albo rzuca wyjątek
    
    def clean(self): 
        """sprawdź poprawność danych i ew., pododawaj info o błędach do formularza"""
        n = self.cleaned_data['name'].strip()
        
        p1 = self.cleaned_data['pwd']
        if len(p1) < 5:
            self.add_error('pwd', 'Hasło jest za krótkie')
        p2 = self.cleaned_data['pwdEnsure']
        if p1 != p2:
            self.add_error('pwdEnsure', 'Powtórzone hasło nie jest zgodne z podanym')
            
        try:
            dane = User.objects.filter(name=n)
            if not dane:
                u = User.objects.create(name=n, pwd=p1)
                whatid = u.id
            else:
                whatid = -1
                self.add_error('name', 'Nazwa użytkownika jest zajęta!')
        except:
            self.add_error('name', 'Nazwa użytkownika jest zajęta!')
            whatid = -1
            # tutaj dodajemy bo inaczej użytkownikowi mogłyby przepaść wypełnione dane
            # jeśli dwóch by chciało ten sam login w tym samym czasie, oba formularze by przeszły a potem kuku
            # tudzież login; a może chce tylko dopisać '1234'    
            
        return {'id': whatid, 'name': n } # zwracamy już bez hasła, bo się nim zajęliśmy
        
