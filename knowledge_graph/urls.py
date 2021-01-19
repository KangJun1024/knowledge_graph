from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('apl/login/', views.login),
    path('apl/chart/', views.chart),
    path('apl/statistics/', views.statistics),
    path('apl/', include('project.urls')),
]