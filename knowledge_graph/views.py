from django.http import JsonResponse

from knowledge_graph import models
from project import models as project
from utils import time_utils
import datetime


def login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    user_obj = models.UserInfo.objects.filter(username=username, password=password).first()
    if not user_obj:
        return JsonResponse({'result':'failure'})
    else:
        return JsonResponse({'result':'success'})

def statistics(request):
    #项目数量
    count = project.Project.objects.count()
    print(count)
    #三元组数 todo
    #概念数 todo

    return JsonResponse({'result':'success','projects':count,'triples':100,'concepts':1200})

def chart(request):
    # 0.1获取时间日期
    today = datetime.datetime.today().date()
    dataList = dateRange(today)
    print(dataList)
    dict = {}
    # 0.2遍历获取日期对应项目数量  获取区间查询
    for i in dataList:
        print(i)
        # 获取项目数量范围查询
        date = time_utils.str2date(i)
        datatime_start = time_utils.date2datetime(date)
        datatime_end = time_utils.delta_day(datatime_start,1)
        print(datatime_start)
        print(datatime_end)
        project.Project.objects.filter()



    return JsonResponse({'result':'success','projects':12,'triples':100,'concepts':1200})

'''
    获取前一个星期时间列表api
'''
def dateRange(beginDate):
    """
    设计时间格式，也就是取出今天前七天的时间列表
    :param beginDate:
    :return:
    """
    yes_time = beginDate + datetime.timedelta(days=+1)
    aWeekDelta = datetime.timedelta(weeks=1)
    aWeekAgo = yes_time - aWeekDelta
    dates = []
    i = 0
    begin = aWeekAgo.strftime("%Y-%m-%d")
    dt = datetime.datetime.strptime(begin, "%Y-%m-%d")
    date = begin[:]
    while i < 7:
        dates.append(date)
        dt = dt + datetime.timedelta(1)
        date = dt.strftime("%Y-%m-%d")
        i += 1
    return dates