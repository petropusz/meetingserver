from django import forms
from meetingserver.models import User

class LoginForm(forms.Form):
    name = forms.CharField(label="login", max_length=50, required = True)
    pwd = forms.CharField(label="hasło", max_length=50, widget=forms.PasswordInput, required = True)
    def clean(self):
        n = self.cleaned_data['name'].strip()
        dane = User.objects.get(name=n)  # name to klucz, więc możemy tak
        if not dane:
            raise forms.ValidationError('Błędne dane logowania')
        p = self.cleaned_data['pwd']
        pReal = dane.pwd
        if p != pReal:
            raise forms.ValidationError('Błędne dane logowania')
        return {'name': n, 'pwd': p}
    
