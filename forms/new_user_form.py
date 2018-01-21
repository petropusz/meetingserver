from django import forms
from meetingserver.models import User

class NewUserForm(forms.Form):
    name = forms.CharField(label="login", max_length=50)
    pwd = forms.CharField(label="hasło", max_length=50, widget=forms.PasswordInput)
    pwdEnsure =  forms.CharField(label = "powtórz hasło", max_length=50, widget=forms.PasswordInput)
    
    #najpierw są uruchamiane clean_field, a potem clean; można też nie robić clean_field żeby nie trzeba spr form.errors
    
    #nic nie robi albo rzuca wyjątek
    def cleanName(self, n): #clean_name by sam wywołał, a ja chcę żeby wywołał tylko clean bo wtedy jest po kolei i w ogóle
        #n = self.cleaned_data['name'].strip()
        
        dane = User.objects.filter(name=n)
        if dane:
            raise forms.ValidationError('Nazwa użytkownika jest zajęta')
        #try:
        #    
        #except Error:
        #    
        # po przekierowaniu do funkcji co tworzy też może pójść błąd!
        return
        
    def clean(self): #TODO prawdzić czy się może nazywać z takim po clean_
        n = self.cleaned_data['name'].strip()
        
        self.cleanName(n)  # niepotrzebne w sumie jak tam niżej tworzymy
        
        
        
        p1 = self.cleaned_data['pwd']
        if len(p1) < 5:
            raise forms.ValidationError('Hasło jest za krótkie')
        p2 = self.cleaned_data['pwdEnsure']
        if p1 != p2:
            raise forms.ValidationError('Powtórzone hasło nie jest zgodne z podanym')
            
            
            
        try:
            User.objects.create(name=n, pwd=p1)
        except:
            raise forms.ValidationError('Nazwa użytkownika jest zajęta') # tutaj dodajemy bo inaczej użytkownikowi mogłyby przepaść wypełnione dane
                                                                         # jeśli dwóch by chciało ten sam login w tym samym czasie, oba formularze by przeszły a potem kuku
                                                                         # tudzież login; a może chce tylko dopisać '1234'    
            
        return {'name': n } # zwracamy już bez hasła, bo się nim zajęliśmy
        
