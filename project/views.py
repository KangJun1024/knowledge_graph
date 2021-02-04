from django.http import JsonResponse, HttpRequest
from knowledge_graph import settings
from .models import Project,Field,Organization
from utils import time_utils,common_utils,import_utils,query_utils,copy_utils,edit_utils
from django.db.models import Q
import os
import simplejson
import logging

# 日志
error_logger = logging.getLogger('error')
access_logger = logging.getLogger('gunicorn')


# 上传文件
def upload(request):
    if request.method == 'POST':
        try:
            # 获取项目名称
            project_id = request.POST.get("project_id")
            access_logger.info("上传图谱项目ID")
            access_logger.info(project_id)
            # 获取文件上传到服务器
            print("-----------开始任务2------------")
            files = request.FILES.getlist('file',None)
            # 生成项目上传文件夹
            print("-----------开始任务3------------")
            LOG_DIR = os.path.join(settings.IMPORT_DIR, project_id)
            print(LOG_DIR)
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)
            path = open(os.path.join(LOG_DIR,files[0].name), 'wb+') # 项目目录下
            for chunk in files[0].chunks():
                path.write(chunk)
            path.close()
            # 解析文件&批量新增数据到neo4j
            print("-----------开始任务------------")
            print(files[0].name)
            result = import_utils.excel_to_csv(os.path.join(LOG_DIR,files[0].name))
            print("-----------开始load csv------------")
            import_utils.load_csv(project_id,result)
            print("-----------结束任务------------")
            # 修改项目状态
            updateStatus(project_id,3)
            #  查询项目三元组数和概念数 编辑项目
            # 三元组数
            triples = query_utils.get_nd_rel_ct([project_id], 1)
            # 概念数
            concepts = query_utils.get_nd_rel_ct([project_id], 0)
            updateNum(project_id,triples,concepts)
            return JsonResponse({'result': 'success'})
        except Exception as e:
            error_logger.error(e)
            updateStatus(project_id, 2)
            return JsonResponse({'result':'failure'})


# 项目新增
def create(request:HttpRequest):
    print(request.body)
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            # 校验项目名称 + 组织编码
            name = payload['project_name']
            code = payload['project_code']
            id = common_utils.generate_record_id('PJ')
            project = Project()
            project.project_name = payload['project_name']
            project.project_code = payload['project_code']
            project.project_status = 1
            project.project_introduction = payload['project_introduction']
            project.project_photo = payload['project_photo']
            project.project_fieldcode = payload['project_fieldcode']
            project.project_fieldname = payload['project_fieldname']
            project.create_user = payload['create_user']
            project.project_id = id
            project.project_concepts = 0
            project.project_triples = 0
            project.create_time = time_utils.now()
            if Project.objects.filter(Q(project_name__icontains=name) & Q(project_code__icontains=code) & ~Q(project_status=0)).exists():
                return JsonResponse({'result': 'failure','message':'同组织下已有同名项目，请重新填写'})
            project.save()
            return JsonResponse({'result': 'success','data':id})
        except Exception as e:
            error_logger.error(e)
            return JsonResponse({'result': 'failure'})


# 项目列表
def list(request):
    # 获取参数
    projectFieldcode = request.GET.get("project_fieldcode")
    projectName = request.GET.get("project_name")
    base_query = Project.objects.order_by('project_status',"-create_time")
    if projectFieldcode is not None and projectName is not None:
        base_query = base_query.filter(Q(project_name__icontains=projectName) &
                          Q(project_fieldcode__icontains=projectFieldcode) & ~Q(project_status=0))
    else:
        base_query = base_query.filter(~Q(project_status=0))
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    # 获取各个项目三元组数和概念数
    for obj in objs:
        id = obj['project_id']
        print(obj['project_id'])
        arr = [str(id)]
        # 三元组数
        triples = query_utils.get_nd_rel_ct(arr, 1)
        print(triples)
        # 概念数
        concepts = query_utils.get_nd_rel_ct(arr, 0)
        print(concepts)
        obj['project_triples'] = triples
        obj['project_concepts'] = concepts

    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)

# 项目删除
def delete(request):
    # 获取参数
    id = request.GET.get("id")
    update_user = request.GET.get("update_user")
    base_query = Project.objects
    obj = base_query.filter(id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '项目不存在'})
    obj.project_status = 0
    obj.update_time = time_utils.now()
    obj.update_user = update_user
    obj.save()
    return JsonResponse({'result': 'success'})


# 项目详情
def detail(request):
    # 获取参数
    id = request.GET.get("id")
    base_query = Project.objects
    obj = base_query.filter(id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '无项目'})
    data = obj.to_dict()
    # 获取 项目id project_id
    project_id = data['project_id']
    print(project_id)

    # arr = [project_id]
    # # 三元组数
    # triples = query_utils.get_nd_rel_ct(arr, 1)
    # print(triples)
    # # 概念数
    # concepts = query_utils.get_nd_rel_ct(arr, 0)
    # print(concepts)
    # data['project_triples'] = triples
    # data['project_concepts'] = concepts
    trees = query_utils.get_prj_kg(project_id)
    data['trees'] = trees
    # print(data)

    return JsonResponse({'result': 'success', 'data': data})

# 项目删除
def update(request):
    # 获取参数
    print(request.body)
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            # 校验项目名称 + 组织编码
            id = payload['id']
            base_query = Project.objects
            project = base_query.filter(id=id).first()
            if not project:
                return JsonResponse({'result': 'failure', 'message': '项目不存在'})
            name = payload['project_name']
            code = payload['project_code']
            # 判断是否有名称 组织编码修改
            if name != project.project_name or code != project.project_code:
                if Project.objects.filter(Q(project_name__icontains=name) & Q(project_code__icontains=code) & ~Q(project_status=0)).exists():
                    return JsonResponse({'result': 'failure', 'message': '项目名称重复'})
            project.project_name = payload['project_name']
            project.project_code = payload['project_code']
            project.project_status = 1
            project.project_introduction = payload['project_introduction']
            project.project_photo = payload['project_photo']
            project.project_fieldcode = payload['project_fieldcode']
            project.project_fieldname = payload['project_fieldname']
            project.update_user = payload['update_user']
            project.project_concepts = 0
            project.project_triples = 0
            project.update_time = time_utils.now()
            project.save()
            return JsonResponse({'result': 'success', 'data': id})
        except Exception as e:
            error_logger.error(e)
            return JsonResponse({'result': 'failure'})


#  通过项目名称获取项目并修改项目状态
def updateStatus(id,status):
    # 获取参数
    base_query = Project.objects
    obj = base_query.filter(project_id=id).first()
    if not obj:
        return JsonResponse({'result': 'failure', 'message': '项目不存在'})
    obj.project_status = status
    obj.update_time = time_utils.now()
    obj.save()
    return JsonResponse({'result': 'success'})

# 项目领域查询
def fieldList(request):
    # 获取参数
    base_query = Field.objects
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)

# 项目组织查询
def orgList(request):
    # 获取参数
    base_query = Organization.objects
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)

# 通过领域获取项目列表 一对多
# 项目列表
def queryList(projectFieldcode):
    # 获取参数
    # projectFieldcode = request.GET.get("project_fieldcode")
    print(projectFieldcode)
    base_query = Project.objects
    if projectFieldcode is not None:
        base_query =  base_query.filter(Q(project_fieldcode__icontains=projectFieldcode) & Q(project_status=3))
    else:
        base_query = base_query.filter(Q(project_status=3))
    objs = [i.to_dict() for i in base_query.all()]
    return objs

# 应用归一查询 搜索概念
def queryConcept(request):
    try:
        # 获取参数
        # 领域 概念
        projectFieldcode = request.GET.get("project_fieldcode")
        print(projectFieldcode)
        conceptName = request.GET.get("concept_name")
        # 通过领域获取项目列表
        objs = queryList(projectFieldcode)
        # 获取
        # print(objs)
        trees = query_utils.query_normalize_all(objs, conceptName)
        total = len(trees)
        return JsonResponse({'result':'success','data':trees,'total':total})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result':'failure'})

# 应用归一查询 概念详情
def queryConceptInfo(request):
    try:
        # 获取参数
        # 领域 概念
        projectFieldcode = request.GET.get("project_fieldcode")
        projectId = request.GET.get("project_id")
        nodeId = request.GET.get("node_id")
        conceptName = request.GET.get("concept_name")
        projectName = request.GET.get("project_name")
        tree = query_utils.query_normalize_detail(projectId,projectName,projectFieldcode,conceptName,nodeId)
        return JsonResponse({'result': 'success','data':tree})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result':'failure'})

# 项目选中图谱数据
def queryProjectConceptInfo(request):
    try:
        # 获取参数
        # 项目 概念
        nodeId = request.GET.get("node_id")
        projectId = request.GET.get("project_id")
        data = query_utils.select_node(nodeId,projectId)
        return JsonResponse({'result': 'success','data':data})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result':'failure'})

# 项目聚焦图谱数据聚焦
def focusProjectConceptInfo(request):
    try:
        # 获取参数
        # 项目 概念
        nodeId = request.GET.get("node_id")
        projectId = request.GET.get("project_id")
        data = query_utils.focus_node(nodeId,projectId)
        return JsonResponse({'result': 'success','data':data})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result':'failure'})

# 复制项目图谱数据
def copy(request):
    try:
        # 获取参数
        # old项目 new项目 路径
        newId = request.GET.get("new_project_id")
        oldId = request.GET.get("old_project_id")
        path = settings.IMPORT_DIR
        copy_utils.copy_prj(oldId,newId,path)
        # 修改项目状态
        updateStatus(newId, 3)
        #  查询项目三元组数和概念数 编辑项目
        # 三元组数
        triples = query_utils.get_nd_rel_ct([newId], 1)
        # 概念数
        concepts = query_utils.get_nd_rel_ct([newId], 0)
        updateNum(newId, triples, concepts)
        return JsonResponse({'result': 'success'})
    except Exception as e:
        error_logger.error(e)
        updateStatus(newId, 2)
        return JsonResponse({'result':'failure'})

# 项目搜索图谱
def selectProjectConceptInfo(request):
    try:
        # 获取参数
        # 项目 概念
        projectId = request.GET.get("project_id")
        conceptName = request.GET.get("concept_name")
        tree = query_utils.query_node(conceptName,projectId)
        return JsonResponse({'result': 'success','data':tree})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result':'failure'})

#  通过项目名称获取项目并修改项目图谱地址
def updatePhoto(request):
    # 获取参数
    print(request.body)
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            # 校验项目名称 + 组织编码
            id = payload['id']
            photo = payload['photo']
            base_query = Project.objects
            project = base_query.filter(id=id).first()
            if not project:
                return JsonResponse({'result': 'failure', 'message': '项目不存在'})
            project.project_photo = photo
            project.update_time = time_utils.now()
            project.save()
            return JsonResponse({'result': 'success'})
        except Exception as e:
            error_logger.error(e)
            return JsonResponse({'result': 'failure'})

# 项目图谱编辑20200121
def updateProjectConcepts(request):
    # 获取参数
    if request.method == 'POST':
        try:
            payload = simplejson.loads(request.body)
            access_logger.info(payload)
            #项目ID
            projectId = payload['prj_id']
            #图谱编辑数据
            editList = payload['edit_list']
            #按序操作图谱数据
            if editList is not None and len(editList) > 0:
                for edit in editList:
                    if("add" == edit["edit_type"] and "node" == edit["obj_type"]):
                        #节点新增
                        edit_utils.creatNode(edit,projectId)
                    elif("del" == edit["edit_type"] and "node" == edit["obj_type"]):
                        #节点删除
                        edit_utils.delete_node(edit,projectId)
                    elif ("add" == edit["edit_type"] and "rel" == edit["obj_type"]):
                        #关系新增
                        edit_utils.creatRel(edit,projectId)
                    elif ("del" == edit["edit_type"] and "rel" == edit["obj_type"]):
                        #关系删除
                        edit_utils.delete_rel(edit,projectId)
            #  查询项目三元组数和概念数 编辑项目
            # 三元组数
            triples = query_utils.get_nd_rel_ct([projectId], 1)
            # 概念数
            concepts = query_utils.get_nd_rel_ct([projectId], 0)
            updateNum(projectId, triples, concepts)
            return JsonResponse({'result': 'success'})
        except Exception as e:
            error_logger.error(e)
            return JsonResponse({'result': 'failure'})


#编辑项目三元组数&概念数
def updateNum(projectId,triples:int,concepts:int):
    # 获取参数
    try:
        # 校验项目名称 + 组织编码
        id = projectId
        triples = triples    # 项目三元组数
        concepts = concepts  # 项目概念数
        base_query = Project.objects
        project = base_query.filter(project_id=id).first()
        if not project:
            return JsonResponse({'result': 'failure', 'message': '项目不存在'})
        project.project_triples = triples
        project.project_concepts = concepts
        project.update_time = time_utils.now()
        project.save()
        return JsonResponse({'result': 'success'})
    except Exception as e:
        error_logger.error(e)
        return JsonResponse({'result': 'failure'})

# 项目列表
def listV2(request):
    # 获取参数
    projectFieldcode = request.GET.get("project_fieldcode")
    projectName = request.GET.get("project_name")
    base_query = Project.objects.order_by('project_status',"-create_time")
    if projectFieldcode is not None and projectName is not None:
        base_query = base_query.filter(Q(project_name__icontains=projectName) &
                          Q(project_fieldcode__icontains=projectFieldcode) & ~Q(project_status=0))
    else:
        base_query = base_query.filter(~Q(project_status=0))
    total = base_query.count()
    objs = [i.to_dict() for i in base_query.all()]
    # 获取各个项目三元组数和概念数
    # for obj in objs:
    #     id = obj['project_id']
    #     print(obj['project_id'])
    #     arr = [str(id)]
    #     # 三元组数
    #     triples = query_utils.get_nd_rel_ct(arr, 1)
    #     print(triples)
    #     # 概念数
    #     concepts = query_utils.get_nd_rel_ct(arr, 0)
    #     print(concepts)
    #     obj['project_triples'] = triples
    #     obj['project_concepts'] = concepts

    data = {
        'result':'success',
        'total': total,
        'data': objs
    }
    return JsonResponse(data)



# def listV2(request):
#     # 项目数量
#     projectId = "PJ99a2f03a614a11eb981cfa163eac98f2"
#     # 三元组数
#     triples = query_utils.get_nd_rel_ct([projectId], 1)
#     # 概念数
#     concepts = query_utils.get_nd_rel_ct([projectId], 0)
#     updateNum(projectId, triples, concepts)
#
#     return JsonResponse({'result': 'success'})

