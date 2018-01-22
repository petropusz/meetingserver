from django import forms
from meetingserver.models import User
from meetingserver.models import Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import Invitation
from django.db import transaction

class NewEventForm(forms.Form):
    name = forms.CharField(label="nazwa", max_length=50, required = False)
    begin = forms.DateTimeField(label="początek", required = False)
    end = forms.DateTimeField(label="koniec", required = False)
    u1 = forms.CharField(label="użytkownik 1", max_length=50, required = False)
    userFieldNr = forms.CharField(widget=forms.HiddenInput(), initial=1)
    
    #def __init__(self, *args, **kwargs):
        #self.uNr = 1
        #super(NewEventForm, self).__init__(*args, **kwargs)
    
    """
    def add_user(self):
        #print ('u'+str(self.uNr))
        self.fields['userFieldNr'].initial = str(int(self.fields['userFieldNr'].initial) + 1) # ++ się kompiluje, ale nie modyfikuje...
        #self.userFieldNr += 1
        print (self.data['userFieldNr'])
        print (self.fields['userFieldNr'].initial)
        #self.uNr = self.data['userFieldNr'] + 1
        #self.data['userFieldNr'] = str(self.data['userFieldNr'] + 1)
        #print ('u'+str(self.uNr))
        self.fields['u'+str(self.data['userFieldNr'] )] = forms.CharField(label="użytkownik "+str(self.uNr), max_length=50, required = False)
        
    def del_user(self):
        #self.userFieldNr -= 1
        self.uNr = self.data['userFieldNr'] - 1
        print ('u'+str(self.uNr))
        if self.uNr <= 1:
            return
        del self.fields['u'+str(self.uNr)]
        self.uNr -= 1 # ++ się kompiluje, ale nie modyfikuje...
        print ('u'+str(self.uNr))
    """
    
    def ensure_user_field_nr(self, uNr):
        for i in range(1, uNr+1):
            key = 'u'+str(i)
            if key not in self.fields:
                #print ("!!!"+ key)
                self.fields[key] = forms.CharField(label="użytkownik "+str(i), max_length=50, required = False)
            else:
                #print (":::"+ key)
                pass
            
           
        
    @transaction.atomic    
    def create_event(self, myuId, uNr):
        # to nie może łapać wyjątku w środku jak z dekoratorem, musi być łapany na zewnątrz
        print ("A")
        name1 = self.cleaned_data['name']
        begin1 = self.cleaned_data['begin']
        end1 = self.cleaned_data['end']
        print ("B")
        print ("HMM")
        print ("+"+str(myuId)) # bez str się na tym wywalał...
        print ("WUT")
        myu = User.objects.get(id=myuId)
        print ("C"+name1+str(begin1)+str(end1))   # TODO MA NIE BYĆ NONE BO NIE ZADZIAŁA
        # zakładam że twórca wydarzenia niekoniecznie musi na nie iść, i traktuję go jako każdego innego
        # w szczególności może go w ogóle nie być w uczestnikach
        meet = Meeting.objects.create(name=name1, begin=begin1, end=end1, invitedNr=uNr, acceptedNr=0, creator=myu)
        print ("D")
        for i in range(1, uNr+1):
            uname = self.cleaned_data['u'+str(i)].strip()
            print ("E")
            u = User.objects.get(name=uname)  # name to klucz, więc możemy tak
            InviteInfo.objects.create(user=u, meeting=meet) # czasu jak rozumiem nie trzeba jak jest auto_now przy aktualizacji
            Invitation.objects.create(user=u, meeting=meet)
        
    def checkClean(self, uNr):
        #self.errors = {} #how to clean it?!?!
        d = {}
        for i in range(1, uNr+1):
            if 'u'+str(i) in self.cleaned_data:
                uname = self.cleaned_data['u'+str(i)].strip()
                self.cleaned_data['u'+str(i)] = uname
                if uname in d: # TODO spr czy takie in jest ok
                    self.add_error('u'+str(i), 'Nazwa użytkownika się powtarza:')
                else:    
                    try:
                        User.objects.get(name=uname)  # name to klucz, więc możemy tak
                    except:
                        self.add_error('u'+str(i), 'Użytkownik nie istnieje:')
            else:
                pass # nazwa może być pusta, ale to się chyba nie zdaży, bo jest w kluczach wtedy zdaje się
        
        #if 'begin' in self.cleaned_data: # TODO date musi mieć sens!!
        
        if 'begin' in self.cleaned_data:
            b = self.cleaned_data['begin']
            if not b:
                self.add_error('begin', 'Brak podanego czasu rozpoczęcia:')
        #else:
        #    print ("WHY DO YOU GO BOTH IN IF AND ELSE?!?!?!?!")
        #    self.add_error('begin', 'Brakuje czasu rozpoczęcia')
            
        if 'end' in self.cleaned_data:
            b = self.cleaned_data['end']
            if not b:
                self.add_error('end', 'Brak podanego czasu zakończenia:')
        #else:
        #    self.add_error('end', 'Brakuje czasu zakończenia')
        
        if 'name' in self.cleaned_data:
            n = self.cleaned_data['name'].strip()
            self.cleaned_data['name'] = n
            if not n:
                self.add_error('name', 'Nazwa wydarzenia zawiera same białe znaki')    
        else:
            self.add_error('name', 'Brakuje nazwy')
        
    def clean(self):
        #self.checkClean()
        #self.checkClean()
        # początku nie walidujemy, bo zaprosić można na każdą chwilę nawet jak im nie pasuje
        
        # TODO dodanie wydarzenia - ponownie - jak już zatwierdzamy formularz, to zanim zatwierdzimy ma być zrobione,
        # bo mogłoby się coś zmienić i użytkownik by został z błędem i bez prawie wypełnionego formularza
        """
        try:
            self.create_event()
        except:
            self.checkClean()
        """
        #name1 = self.cleaned_data['name'].strip()
        #tu nic nie robimy, żeby można było robić submit bez sprawdzania!
        #return self.cleaned_data #{'event_name': name1 } #to jest jak już przejdzie - dostajemy info na stronę jakiego wydarzenia przekierować
        
    
    
