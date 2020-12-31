from django.http import JsonResponse

from knowledge_graph import models
from project import models as project
from utils import time_utils
import logging
import simplejson
from django.db.models import Q
logger = logging.getLogger(__name__)


def login(request):
    payload = simplejson.loads(request.body)
    username = payload['username']
    password = payload['password']
    user_obj = models.UserInfo.objects.filter(username=username, password=password).first()
    if not user_obj:
        return JsonResponse({'result':'failure'})
    else:
        return JsonResponse({'result':'success','data':username})

def statistics(request):
    #项目数量
    count = list(project.Project.objects.filter(~Q(project_status=0)))
    count = len(count)
    # #三元组数
    # triples = query_utils.get_nd_rel_ct([],1)
    # #概念数
    # concepts = query_utils.get_nd_rel_ct([],0)

    return JsonResponse({'result':'success','projects':count,'triples':100,'concepts':1200})

def chart(request):
    # 定义字典
    result = {}
    # 获取统计时间段
    data_year_month = time_utils.monthRange()
    print(data_year_month)
    for i in data_year_month:
        datatimeStart = time_utils.month2DateTime(i)
        datatimeEnd = time_utils.delta_month(datatimeStart,1)
        # 获取项目数量
        project_count = list(project.Project.objects.filter(create_time__range=(datatimeStart,datatimeEnd)))
        project_count = len(project_count)
        result[i] = project_count


    return JsonResponse({'result':'success','data':result})

