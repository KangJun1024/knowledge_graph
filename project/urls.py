from django.urls import path, include
from . import views

urlpatterns = [
    path('project/upload/', views.upload), #上传
    path('project/list/', views.list), #项目列表
    path('project/queryList/', views.queryList), #项目列表内部使用
    path('project/queryConcept/', views.queryConcept), #查询图谱关联列表数据
    path('project/queryConceptInfo/', views.queryConceptInfo), #查询图谱详情
    path('project/create/', views.create), #创建项目
    path('project/delete/', views.delete), #删除项目
    path('project/detail/', views.detail), #项目详情
    path('project/update/', views.update), #项目修改
    path('project/fieldList/', views.fieldList), #领域列表
]