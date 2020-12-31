from django.urls import path, include
from . import views

urlpatterns = [
    path('project/upload/', views.upload), #上传
    path('project/list/', views.list),
    path('project/queryList/', views.queryList),
    path('project/create/', views.create),
    path('project/delete/', views.delete),
    path('project/detail/', views.detail),
    path('project/update/', views.update),
    path('project/fieldList/', views.fieldList),
]