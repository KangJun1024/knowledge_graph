from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('apl/login/', views.login),
    path('apl/check_login/', views.check_login),
    path('apl/logout/', views.logout),
    path('apl/chart/', views.chart),
    path('apl/statistics/', views.statistics),
    path('apl/statisticsV2/', views.statisticsV2),
    path('apl/', include('project.urls')),
]