from django.http import JsonResponse, HttpRequest
from knowledge_graph import settings
from project import models
from .models import Project
from base import errors
import os
import simplejson


# 上传文件
def upload(request):
    if request.method == 'POST':
        # 获取文件上传到服务器
        files = request.FILES.getlist('file',None)
        print(files)
        if not files:
            return JsonResponse({'result':'failure'})
        destination = open(os.path.join(settings.BASE_DIR,files[0].name), 'wb+') # 项目目录下
        for chunk in files[0].chunks():
            destination.write(chunk)
        destination.close()
        # 解析文件&批量新增数据到neo4j todo

        return JsonResponse({'result':'success'})
    else:
        return JsonResponse({'result':'failure'})


# 项目新增
def create(request:HttpRequest):
    if request.method == 'POST':
        payload = simplejson.loads(request.body)
        # 校验项目名称
        name = payload['project_name']
        project = Project()
        project.project_name = payload['project_name']
        project.project_code = payload['project_code']
        project.project_status = 1
        project.project_introduction = payload['project_introduction']
        project.project_photo = payload['project_photo']
        project.project_fieldcode = payload['project_fieldcode']
        project.project_fieldname = payload['project_fieldname']
        project.create_user = payload['create_user']
        if Project.objects.filter(project_name=name).exists():
            return JsonResponse({'result': 'failure','message':'项目名称重复'})
        project.save()
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failure'})


# 项目列表
def list(request):
    if request.method == 'POST':


        return JsonResponse({'result':'success'})
    else:
        return JsonResponse({'result':'failure'})

# 项目删除
def delete(request):
    if request.method == 'POST':


        return JsonResponse({'result':'success'})
    else:
        return JsonResponse({'result':'failure'})

# 项目详情
def detail(request):
    if request.method == 'POST':


        return JsonResponse({'result':'success'})
    else:
        return JsonResponse({'result':'failure'})