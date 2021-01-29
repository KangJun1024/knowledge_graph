from django.urls import path, include
from . import views

urlpatterns = [
    path('project/upload/', views.upload), #上传
    path('project/list/', views.list), #项目列表
    path('project/queryList/', views.queryList), #项目列表内部使用
    path('project/queryConcept/', views.queryConcept), #归一应用查询图谱关联列表数据
    path('project/queryConceptInfo/', views.queryConceptInfo), #归一应用查询图谱详情
    path('project/create/', views.create), #创建项目
    path('project/copy/', views.copy), #复制项目
    path('project/delete/', views.delete), #删除项目
    path('project/detail/', views.detail), #项目详情
    path('project/update/', views.update), #项目修改
    path('project/updatePhoto/', views.updatePhoto), #修改项目图片地址
    path('project/fieldList/', views.fieldList), #领域列表
    path('project/orgList/', views.orgList), #组织列表
    path('project/queryProjectConceptInfo/',views.queryProjectConceptInfo),  #项目选中
    path('project/focusProjectConceptInfo/',views.focusProjectConceptInfo),  #项目聚焦 需要返回图谱数据
    path('project/updateProjectConcepts/',views.updateProjectConcepts),  #项目图谱编辑 (添加节点/关系,删除节点/关系)
    path('project/selectProjectConceptInfo/',views.selectProjectConceptInfo)  #项目搜索 需要返回图谱数据
]