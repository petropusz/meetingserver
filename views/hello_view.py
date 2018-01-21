from django.http import HttpResponse

from meetingserver.models import User

def hello(request):
    s1 = User(name="User1")
    s1.save()
    userList = User.objects.all()
    html = "<html><body><h1>No żegnam</h1>"
    for user in userList:
        html += "<h2>" + user.name + "</h2>"
    html += "</body></html>"
    return HttpResponse(html)
