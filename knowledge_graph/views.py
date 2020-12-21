from django.http import JsonResponse

from knowledge_graph import models


def login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    user_obj = models.UserInfo.objects.filter(username=username, password=password).first()
    if not user_obj:
        return JsonResponse({'result':'failure'})
    else:
        return JsonResponse({'result':'success'})