from django.db import models


class Project(models.Model):
    project_name = models.CharField(max_length=50,null=False)
    project_fieldcode = models.CharField(max_length=50,null=False)
    project_fieldname = models.CharField(max_length=50,null=False)
    project_introduction = models.CharField(max_length=2000)
    project_code = models.CharField(max_length=50,null=False)
    project_photo = models.CharField(max_length=255)
    project_status = models.CharField(max_length=1) # 1 上传中 2 失败  3 完成
    create_time = models.DateTimeField(auto_now_add=True)  # 用于表示创建时间
    update_time = models.DateTimeField(auto_now=True)  # 用于表示更新时间
    create_user = models.CharField(max_length=50)
    update_user = models.CharField(max_length=50)
