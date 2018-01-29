"""meetingserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from views import main_page
from views import logged_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_page.get_main_page),
    path('sign_up', main_page.sign_up),
    path('sign_out', main_page.sign_out),
    path('me', logged_views.me),
    path('create_event', logged_views.create_event),
    path('create_event/add_user_field', logged_views.add_user_field),
    path('create_event/del_user_field', logged_views.delete_user_field),
    path('create_event/find_plan_gap', logged_views.find_gap_in_plans),
    path('create_event/find_inv_gap', logged_views.find_gap_in_invs),
    path('show_event', logged_views.show_event),
    path('my_created_events', logged_views.my_created_events),
    path('ask_delete_user', logged_views.ask_delete_user),
    path('delete_user', logged_views.delete_user),    
    path('ok_deleted_att_event_info', logged_views.ok_deleted_att_event_info)
]


