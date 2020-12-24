import pytz
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

loc_tz = pytz.timezone('Asia/Shanghai')
utc_tz = pytz.timezone('UTC')


def str2datetime_by_format(dt_str, dt_format='%Y-%m-%d %H:%M:%S'):
    '''
    时间字符串转datetime
    '''
    return loc_tz.localize(datetime.strptime(dt_str, dt_format))


def datetime2str_by_format(dt, dt_format='%Y-%m-%d %H:%M:%S'):
    '''
    本地datetime转本地字符串
    '''
    if not dt:
        return ''
    return dt.astimezone(loc_tz).strftime(dt_format)


def date2str(dt, dt_format='%Y-%m-%d'):
    '''
    日期转字符串
    '''
    if not dt:
        return ''
    return dt.strftime(dt_format)


def str2date(dt_str):
    '''
    字符串转日期
    '''
    dt = str2datetime_by_format(dt_str, '%Y-%m-%d')
    return dt.date()


def date2datetime(dt):
    return today().replace(year=dt.year, month=dt.month, day=dt.day)


def datetime2date_range(dt):
    '''
    datetime转换成一天的开始和结束时间[start, end)
    '''
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def now():
    return datetime.now()


def today():
    dt = now()
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt


def tomorrow():
    return today() + timedelta(days=1)


def yesterday():
    return today() - timedelta(days=1)


def utcts2dt(ts):
    '''
    UTC时间戳转Datetime
    '''
    dt = datetime.utcfromtimestamp(ts)
    dt = dt + timedelta(hours=8)
    return dt


def get_all_week_by_year(year):
    '''
    获取一年所有周字符串列表
    '''
    week_list = []
    for i in range(1, datetime.date(year, 12, 31).isocalendar()[1] + 1):
        week = '{}-{}'.format(year, i)
        week_list.append(week)
    return week_list


def get_all_month_by_year(year):
    '''
    获取一年所有月份字符串列表
    '''
    month_list = []
    for i in range(12):
        month = '{}-{}'.format(year, i + 1)
        month_list.append(month)
    return month_list


def get_all_month(dt_start, dt_end):
    '''
    获取时间范围内所有月份
    '''
    month_list = []
    dvalue = dt_end.year - dt_start.year
    if dvalue == 0:
        for i in range(dt_start.month, dt_end.month + 1):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
    elif dvalue == 1:
        for i in range(dt_start.month, 13):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
        for i in range(1, dt_end.month + 1):
            month = '{}-{}'.format(dt_end.year, i)
            month_list.append(month)
    elif dvalue > 1:
        for i in range(dt_start.month, 13):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
        for i in range(1, dvalue):
            month_list.extend(get_all_month_by_year(dt_start.year + i))
        for i in range(1, dt_end.month + 1):
            month = '{}-{}'.format(dt_end.year, i)
            month_list.append(month)
    return month_list


def get_max_week_by_year(year):
    '''
    获取一年最大周数
    '''
    # 取一年中最后一天的周数，如果所在年已经不是同一年，那么再减去对应星期数
    week = date(year, 12, 31).isocalendar()
    if week[0] == year:
        return week[1]
    else:
        return date(year, 12, 31 - week[2]).isocalendar()[1]


def get_all_week(dt_start, dt_end):
    '''
    获取时间范围内所有周
    '''
    week_list = []
    dvalue = dt_end.year - dt_start.year
    if dvalue == 0:
        for i in range(dt_start.isocalendar()[1], dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
    elif dvalue == 1:
        max_week = get_max_week_by_year(dt_start.year)
        for i in range(dt_start.isocalendar()[1], max_week + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
        for i in range(1, dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_end.year, i)
            week_list.append(week)
    elif dvalue > 1:
        for i in range(dt_start.isocalendar()[1], dt_start.replace(month=12, day=31).isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
        for i in range(1, dvalue):
            week_list.extend(get_all_week_by_year(dt_start.year + i))
        for i in range(1, dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_end.year, i)
            week_list.append(week)
    return week_list

def delta_day(datatime_start,delta=0):
    """
    :param delta:   偏移量
    :return:        0今天, 1昨天, 2前天, -1明天 ...
    """
    return (datatime_start + timedelta(days=delta)).strftime('%Y-%m-%d %H:%M:%S')

def delta_month(datatime_start,delta=0):
    """
    :param delta:   偏移量
    :return:        0今天, 1昨天, 2前天, -1明天 ...
    """
    return (datatime_start + relativedelta(months=+1))

def month2DateTime(month):
    return datetime.strptime(month, '%Y-%m')


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

'''
    得到现在时间12个月前的每个月
'''

def monthRange():
    # 0.1获取时间日期
    # 得到现在的时间  得到now等于2016年9月25日
    now = datetime.now()
    # 得到今年的的时间 （年份） 得到的today_year等于2016年
    today_year = now.year
    # 今年的时间减去1，得到去年的时间。last_year等于2015
    last_year = int(now.year) - 1
    # 得到今年的每个月的时间。today_year_months等于1 2 3 4 5 6 7 8 9，
    today_year_months = range(1, now.month + 1)
    # 得到去年的每个月的时间  last_year_months 等于10 11 12
    last_year_months = range(now.month + 1, 13)
    # 定义列表去年的数据
    data_list_lasts = []
    # 通过for循环，得到去年的时间夹月份的列表
    # 先遍历去年每个月的列表
    for last_year_month in last_year_months:
        # 定义date_list 去年加上去年的每个月
        date_list = '%s-%s' % (last_year, last_year_month)
        # 通过函数append，得到去年的列表
        data_list_lasts.append(date_list)

    data_list_todays = []
    # 通过for循环，得到今年的时间夹月份的列表
    # 先遍历今年每个月的列表
    for today_year_month in today_year_months:
        # 定义date_list 去年加上今年的每个月
        data_list = '%s-%s' % (today_year, today_year_month)
        # 通过函数append，得到今年的列表
        data_list_todays.append(data_list)
    # 去年的时间数据加上今年的时间数据得到年月时间列表
    data_year_month = data_list_lasts + data_list_todays
    return data_year_month