from django.db import models
from utils import time_utils


class Project(models.Model):
    project_name = models.CharField(max_length=50,null=False)
    project_fieldcode = models.CharField(max_length=50,null=False)
    project_fieldname = models.CharField(max_length=50,null=False)
    project_introduction = models.CharField(max_length=2000)
    project_code = models.CharField(max_length=50,null=False)
    project_photo = models.CharField(max_length=255)
    project_status = models.CharField(max_length=1) # 1 上传中 2 失败  3 完成  0 删除
    create_time = models.DateTimeField(auto_now_add=True)  # 用于表示创建时间
    update_time = models.DateTimeField(auto_now=True)  # 用于表示更新时间
    create_user = models.CharField(max_length=50)
    update_user = models.CharField(max_length=50)

    def to_dict(self):
        columns = self._meta.fields
        data = {}
        for column in columns:
            column_name = column.name
            column_typ = column.get_internal_type()
            # 所有使用choices的字段，返回当前值的描述
            if column.choices:
                method = 'get_{}_display'.format(column_name)
                data['{}_desc'.format(column_name)] = getattr(self, method)()
            value = getattr(self, column_name)
            # 统一格式化时间输出
            if column_typ == 'DateTimeField' and value:
                value = time_utils.datetime2str_by_format(value, '%Y-%m-%d %H:%M:%S')
            elif column_typ == 'ForeignKey' and value:
                value = value.id
                column_name = '{}_id'.format(column_name)
            data[column_name] = value
        return data
