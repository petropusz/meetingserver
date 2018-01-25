from django import forms
from meetingserver.models import User
from meetingserver.models import Meeting
from meetingserver.models import InviteInfo
from meetingserver.models import Plan
from meetingserver.models import Invitation
from django.db import transaction
from datetime import datetime
from datetime import timedelta
import pytz  # żeby mieć "timezone-aware" now
from django.utils.dateparse import parse_duration
import copy

def find_first_gap(gap, tab):
    sum = 0
    print ("""!!!!""" + str(tab))
    for i in range(0, len(tab)):
        a,b = tab[i]
        sum += b
        if sum == 0 and i+1 < len(tab):  # szukamy luki, a nie na końcu
            a2,b2 = tab[i+1]
            if a2 - gap >= a:
                return a
    a,b = tab[len(tab)-1]
    return a  # kiedy ostatniemu się ostatnie kończy, skoro nie znaleźliśmy luki     

class NewEventForm(forms.Form):

    gapLength = forms.DurationField(label="długość przedziału czasu", required=False)
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
    
    def getUnames(self, uNr):
        u = set()
        for i in range(1, uNr+1):
            u.add(self.cleaned_data['u'+str(i)].strip())
        return u        
           
    def find_gap_plan(self, uNr):
        gap = parse_duration(self.data['gapLength'])
        self.checkNames(uNr)
        if not gap:
            self.add_error('gapLength', 'Nie podano długości przedziału:')
        if self.errors: # TODO to sprawdzenie nie działa....
            return False 
        print ("+++++++++++"+str(self.errors))
        unames = self.getUnames(uNr)        
        planned = Plan.objects.filter(user__name__in=unames)
        tab = [(datetime.now(pytz.utc), 0)]  # czas kompa, może być inny niby niż czas bazy, ale zał. że jest ok; żeby znalazł teraz jeśli się uda
        for p in planned:
            p_begin = p.meeting.begin
            p_end = p.meeting.end
            tab.append((p_begin, +1))
            tab.append((p_end, -1))
        print ("::::"+ str(sorted(tab)))
        gap_begin = find_first_gap(gap, sorted(tab))    
        #self.fields['begin'] = forms.DateTimeField(label="znaleziony początek", required = False, initial = gap_begin)
        print ("{}{}" + str(gap) + ";" + str(gap_begin) )
        #self.fields['end'] = forms.DateTimeField(label="znaleziony koniec", required = False, initial = gap_begin+gap)
        # formularz musi być z kopii POST, żeby .data było mutable!!
        self.data['begin'] = gap_begin
        self.fields['begin'].label = "znaleziony początek"
        self.data['end'] = gap_begin+gap
        self.fields['end'].label = "znaleziony koniec"
        return True
        
    """ NIE DZIAŁA
    def get_initial(self):
        initial1 = super(NewEventForm, self).get_initial()
        initial1['begin'] = datetime.now(pytz.utc)
        initial1['end'] = self.fields['end'].initial
        return initial1
    """
      
    def find_gap_inv(self, uNr):
        gap = parse_duration(self.data['gapLength'])
        self.checkNames(uNr)
        if not gap:
            self.add_error('gapLength', 'Nie podano długości przedziału:')
        if self.errors:
            return False  
        unames = self.getUnames(uNr)        
        planned = Plan.objects.filter(user__name__in=unames)
        invitations = Invitation.objects.filter(user__name__in=unames)
        tab = [(datetime.now(pytz.utc),0)]  # czas kompa, może być inny niby niż czas bazy, ale zał. że jest ok; żeby znalazł teraz jeśli się uda
        for p in planned:
            p_begin = p.meeting.begin
            p_end = p.meeting.end
            tab.append((p_begin, +1))
            tab.append((p_end, -1))
        for p in invitations:
            p_begin = p.meeting.begin
            p_end = p.meeting.end
            tab.append((p_begin, +1))
            tab.append((p_end, -1))
            
        print ("[][]" + str(gap) + ";" )  
        gap_begin = find_first_gap(gap, sorted(tab))  
        print ("{}{}" + str(gap) + ";" + str(gap_begin) + str(type(gap_begin)) )  
        #del self.fields['begin']
        #del self.fields['end']
        #self.fields['begin'] = forms.DateTimeField(label="znaleziony początek", required = False, initial = gap_begin)
        #self.fields['end'] = forms.DateTimeField(label="znaleziony koniec", required = False, initial = gap_begin+gap)
        
        # formularz musi być z kopii POST, żeby .data było mutable!!
        self.data['begin'] = gap_begin
        self.fields['begin'].label = "znaleziony początek"
        self.data['end'] = gap_begin+gap
        self.fields['end'].label = "znaleziony koniec"
        
        #self.fields['ehh'] = forms.CharField(label="jakie to jest dno to django", required = False, initial = "żałosne") # initial nie działa, bo nie
        #   !!!!   TODO najwyżej wypisać to gdzieś żeby sobie przekleił, jakie to django jest żałosne....
        #del self.initial
        #self.initial = {'begin': gap_begin, 'end': gap_begin+gap}
    #    newform = NewEventForm(initial={'begin': gap_begin, 'end': gap_begin+gap})
        #for field in self.fields:
        #    newform.fields[field] = copy.deepcopy(self[field])
        return True #newform
    
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
        
    def checkNames(self, uNr):
        #self.errors = {} #how to clean it?!?!
        d = set()
        print ("CHECKING")
        for i in range(1, uNr+1):
            if 'u'+str(i) in self.cleaned_data:
                uname = self.cleaned_data['u'+str(i)].strip()
                self.cleaned_data['u'+str(i)] = uname
                if uname in d: # TODO spr czy takie in jest ok
                    print ("TU")
                    self.add_error('u'+str(i), 'Nazwa użytkownika się powtarza:')
                else:    
                    try:
                        User.objects.get(name=uname)  # name to klucz, więc możemy tak
                    except:
                        print ("TU TEŻ")
                        self.add_error('u'+str(i), 'Użytkownik nie istnieje:')
                if uname:
                    d.add(uname)
            else:
                print ("TU TEŻ")
                self.add_error('u'+str(i), 'Nie podano użytkownika:')
        
    def checkClean(self, uNr):
        #self.errors = {} #how to clean it?!?!
        
        self.checkNames(uNr)
        
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
        
    
    
