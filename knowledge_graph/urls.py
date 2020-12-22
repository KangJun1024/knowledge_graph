from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', views.login),
    path('api/chart/', views.chart),
    path('api/project/', include('project.urls')),
]