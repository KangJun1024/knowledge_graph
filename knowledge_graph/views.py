from django.http import JsonResponse

from knowledge_graph import models
from project import models as project
from utils import time_utils,query_utils
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
        resp = JsonResponse({'result': 'success', 'data': username})
        #登录成功之后
        # 在向浏览器返回cookie的同时，也需要向后台表django_session中添加用户的登录状态session_data.
        request.session['username'] = username
        request.session["is_login"] = "1"
        resp.set_cookie('username', username, max_age=1900000)
        return resp


def check_login(request):
    # 获取cookie数据
    username = request.COOKIES.get('username', '')
    var1 = request.session.get("is_login", None)
    var2 = request.session.get("username", None)
    print(username,var1,var2)
    if username == var2 and "1" == var1:
        return JsonResponse({'result': 'success'})
    else:
        return JsonResponse({'result': 'failure'})
# 注销函数
def logout(request):
    # 只删除session数据
    request.session.flush()
    return JsonResponse({'result': 'success'})

def statistics(request):
    #项目数量
    count = list(project.Project.objects.filter(~Q(project_status=0)))
    count = len(count)
    #三元组数
    triples = query_utils.get_nd_rel_ct([],1)
    #概念数
    concepts = query_utils.get_nd_rel_ct([],0)

    return JsonResponse({'result':'success','projects':count,'triples':triples,'concepts':concepts})

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
        base_query = project.Project.objects.filter(~Q(project_status=0))
        project_count = list(base_query.filter(create_time__range=(datatimeStart,datatimeEnd)))
        project_count = len(project_count)
        result[i] = project_count

    return JsonResponse({'result':'success','data':result})

#项目统计数据20210129
def statisticsV2(request):
    #项目数量
    projects = project.Project.objects.filter(~Q(project_status=0))
    count = len(projects)
    print(count)
    #三元组数  获取项目对应三元组数
    triples = 0
    #概念数    获取项目对应概念数
    concepts = 0
    objs = [i.to_dict() for i in projects.all()]
    for pro in objs:
        triples += pro["project_triples"]
        concepts += pro["project_concepts"]

    return JsonResponse({'result':'success','projects':count,'triples':triples,'concepts':concepts})