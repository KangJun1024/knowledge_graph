from django.http import JsonResponse, HttpRequest
from knowledge_graph import settings
from .models import Project
from utils import time_utils
from django.db.models import Q
import os
import simplejson



# 上传文件
def upload(request):
    if request.method == 'POST':
        # 获取文件上传到服务器
        files = request.FILES.getlist('file',None)
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
        name = payload['projectName']
        project = Project()
        project.project_name = payload['project_name']
        project.project_code = payload['project_code']
        project.project_status = 1
        project.project_introduction = payload['project_introduction']
        project.project_photo = payload['project_photo']
        project.project_fieldcode = payload['project_fieldcode']
        project.project_fieldname = payload['project_fieldname']
        project.create_user = payload['create_user']
        project.create_time = time_utils.now()
        if Project.objects.filter(project_name=name).exists():
            return JsonResponse({'result': 'failure','message':'项目名称重复'})
        project.save()
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failure'})


# 项目列表
def list(request):
    # 获取参数
    projectFieldcode = request.GET.get("projectFieldcode")
    projectName = request.GET.get("projectName")
    base_query = Project.objects
    base_query =  base_query.filter(Q(project_name__icontains=projectName) &
                      Q(project_fieldcode__icontains=projectFieldcode) & ~Q(project_status=0))
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)

# 项目删除
def delete(request):
    # 获取参数
    id = request.GET.get("id")
    update_user = request.GET.get("update_user")
    base_query = Project.objects
    obj = base_query.filter(id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '项目不存在'})
    obj.project_status = 0
    obj.update_time = time_utils.now()
    obj.update_user = update_user
    obj.save()
    return JsonResponse({'result': 'success'})


# 项目详情
def detail(request):
    # 获取参数
    id = request.GET.get("id")
    base_query = Project.objects
    obj = base_query.filter(id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '无项目'})
    data = obj.to_dict()
    return JsonResponse({'result': 'success', 'data': data})