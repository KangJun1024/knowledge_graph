from django.http import JsonResponse, HttpRequest
from knowledge_graph import settings
from .models import Project,Field
from utils import time_utils,common_utils
from django.db.models import Q
import os
import simplejson
import logging

# 日志
error_logger = logging.getLogger('error')
access_logger = logging.getLogger('gunicorn')


# 上传文件
def upload(request):
    if request.method == 'POST':
        try:
            # 获取项目名称
            project_id = request.POST.get("project_id")
            print(project_id)
            # 获取文件上传到服务器
            files = request.FILES.getlist('file',None)
            if not files:
                return JsonResponse({'result':'failure'})
            destination = open(os.path.join(settings.BASE_DIR,files[0].name), 'wb+') # 项目目录下
            for chunk in files[0].chunks():
                destination.write(chunk)
            destination.close()
            # 解析文件&批量新增数据到neo4j todo

            # 修改项目状态
            updateStatus(project_id,3)
            return JsonResponse({'result': 'success'})
        except Exception as e:
            updateStatus(project_id, 2)
            return JsonResponse({'result':'failure'})


# 项目新增
def create(request:HttpRequest):
    print(request.body)
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            # 校验项目名称 + 组织编码
            name = payload['project_name']
            code = payload['project_code']
            id = common_utils.generate_record_id('PJ')
            project = Project()
            project.project_name = payload['project_name']
            project.project_code = payload['project_code']
            project.project_status = 1
            project.project_introduction = payload['project_introduction']
            project.project_photo = payload['project_photo']
            project.project_fieldcode = payload['project_fieldcode']
            project.project_fieldname = payload['project_fieldname']
            project.create_user = payload['create_user']
            project.project_id = id
            project.project_concepts = 0
            project.project_triples = 0
            project.create_time = time_utils.now()
            if Project.objects.filter(Q(project_name__icontains=name) & Q(project_code__icontains=code)).exists():
                return JsonResponse({'result': 'failure','message':'项目名称重复'})
            project.save()
            return JsonResponse({'result': 'success','data':id})
        except Exception as e:
            return JsonResponse({'result': 'failure'})


# 项目列表
def list(request):
    # 获取参数
    projectFieldcode = request.GET.get("project_fieldcode")
    projectName = request.GET.get("project_name")
    base_query = Project.objects.order_by('project_status')
    if projectFieldcode is not None and projectName is not None:
        base_query =  base_query.filter(Q(project_name__icontains=projectName) &
                          Q(project_fieldcode__icontains=projectFieldcode) & ~Q(project_status=0))
    else:
        base_query = base_query.filter(~Q(project_status=0))
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

# 项目删除
def update(request):
    # 获取参数
    id = request.GET.get("id")
    update_user = request.GET.get("update_user")

    print(request.body)
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            # 校验项目名称 + 组织编码
            id = payload['id']
            base_query = Project.objects
            project = base_query.filter(id=id).first()
            if not project:
                return JsonResponse({'result': 'failure', 'message': '项目不存在'})
            name = payload['project_name']
            code = payload['project_code']
            if Project.objects.filter(Q(project_name__icontains=name) & Q(project_code__icontains=code)).exists():
                return JsonResponse({'result': 'failure','message':'项目名称重复'})
            project.project_name = payload['project_name']
            project.project_code = payload['project_code']
            project.project_status = 1
            project.project_introduction = payload['project_introduction']
            project.project_photo = payload['project_photo']
            project.project_fieldcode = payload['project_fieldcode']
            project.project_fieldname = payload['project_fieldname']
            project.update_user = payload['update_user']
            project.project_id = id
            project.project_concepts = 0
            project.project_triples = 0
            project.update_time = time_utils.now()
            project.save()
            return JsonResponse({'result': 'success', 'data': id})
        except Exception as e:
            return JsonResponse({'result': 'failure'})


#  通过项目名称获取项目并修改项目状态
def updateStatus(id,status):
    # 获取参数
    base_query = Project.objects
    obj = base_query.filter(project_id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '项目不存在'})
    obj.project_status = status
    obj.update_time = time_utils.now()
    obj.save()
    return JsonResponse({'result': 'success'})

# 项目领域查询
def fieldList(request):
    # 获取参数
    base_query = Field.objects
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)