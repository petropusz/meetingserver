# !/usr/bin/env/python
# -*- coding: utf-8 -*-
""" 
middleware usuwające wydarzenia, które minęły
- usuwa przy starcie aplikacji albo jeśli ostatnie usuwanie było 
  > 2 minuty temu 
"""

from meetingserver.models import Meeting
import pytz  # żeby mieć "timezone-aware" now
from django.utils.dateparse import parse_duration
from datetime import datetime, timedelta 

class PastEventClearer:

    def __init__(self, get_response):

        self.get_response = get_response
        self.clear_past_events()  # clear also on app start
        self.last_cleared = datetime.now(pytz.utc) 

    def __call__(self, request):
        
        if datetime.now(pytz.utc) - self.last_cleared > timedelta(minutes=2):
            self.clear_past_events()
            self.last_cleared = datetime.now(pytz.utc) 
        
        response = self.get_response(request)
        
        #nothing after view rendering
        
        return response
        
    def clear_past_events(self):
        
        Meeting.objects.filter(end__lte=datetime.now(pytz.utc)).delete()  # usuwa też z innych tabel, bo CASCADE
                                                                          
