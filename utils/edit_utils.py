# -*- coding: utf-8 -*-
from py2neo import Graph
from pandas import DataFrame
import pandas as pd

# graph = Graph("bolt://120.221.160.106:8002", username="neo4j", password="123456")
graph = Graph("bolt://127.0.0.1:8002", username="neo4j", password="123456")

#删除关系
def delete_rel(node,prj_label):
    # 解析json数据
    data = node
    # 获取节点数据
    source_uid = data["rel"]["source_uid"]
    target_uid = data["rel"]["target_uid"]
    #计算出度
    cql = "match(n:%s)-->(m:%s) where n.uid = '%s' and n.delete_flag = 0 and m.delete_flag = 0 return m"%(prj_label,prj_label,source_uid)
    result = graph.run(cql).to_ndarray() 
    if len(result) > 1: #判断出度大于1
        cql = "match(n:%s)-[r]->(m:%s) where n.uid = '%s' and m.uid = '%s' and n.delete_flag = 0 and m.delete_flag = 0 delete r"%(prj_label,prj_label,source_uid,target_uid)
        graph.run(cql) #只删除关系
    elif len(result) == 1:
        node["node"]["uid"] = source_uid
        delete_node(node,prj_label) #删除关系下的节点树

#删除节点
def delete_node(node,prj_label):  
    # 解析json数据
    data = node
    # 获取节点数据
    node_uid = data["node"]["uid"]
    #计算id
    cql = "match(n:%s) where n.uid = '%s' and n.delete_flag = 0 return id(n)" %(prj_label,node_uid)
    result = graph.run(cql).to_ndarray()  #通过uid获取id
    if len(result) > 0:
        input_id = result[0][0]
        del_nodes = query_del_nodes(input_id) #获取需删除的树所有id
        cql = "match(n:%s) where id(n) in %s set n.delete_flag = 1" %(prj_label,str(del_nodes))
        graph.run(cql) #删除节点及其子树

#查询需要删除的节点
def query_del_nodes(input_id):
    del_tree = []
    query_children_tree(input_id,del_tree) #查找子节点树
    multi_parent = query_multi_parent(del_tree) #有外部父节点的节点
    if input_id in multi_parent:
        multi_parent.remove(input_id)
    del_tree_set = set(del_tree)
    for p in multi_parent:
        saved_tree = []
        query_children_tree(p,saved_tree) #查询有外部父节点的树
        del_tree_set = del_tree_set - set(saved_tree) #保留有外部父节点的树
    return list(del_tree_set)

#递归查找子节点树
def query_children_tree(input_id:int,tree:[]):
    if not (input_id in tree):
        tree.append(input_id)
        cql = "match(n)<-[r]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m)" %(input_id)
        result = graph.run(cql).to_ndarray() #二维数组
        for r in result:
            query_children_tree(r[0],tree)

#查找递归树中有外部父节点的节点
def query_multi_parent(tree):
    arr = []
    for t in tree:
        cql = "match(n)-[r]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m)" %(t)
        result = graph.run(cql).to_ndarray() #二维数组  
        for r in result:
            if r[0] not in tree: #判断是否有外部父节点
                arr.append(t)
                break
    return arr        

#创建节点20210119
def creatNode(node,prj_label):
    # 解析json数据
    data = node
    # 获取节点数据
    uid = data["node"]["uid"]
    name = data["node"]["name"]
    label = data["node"]["label"]
    # 获取关系数据
    relName = data["rel"]["name"]
    targetId = data["rel"]["target_uid"]  #父节点
    # match 父节点
    sql_match_target = "match(p:%s) where p.uid='%s'" %(prj_label,targetId)
    # 创建节点语句
    sql_create_node = "create(n:%s:%s{name:'%s',uid:'%s',delete_flag:0})-[:%s]->(p)"%(prj_label,label,name,uid,relName)
    sql_create_node = sql_match_target + " " + sql_create_node
    print(sql_create_node)

    graph.run(sql_create_node)

#创建关系20210120
def creatRel(node,prj_label):
    # 解析json数据
    data = node
    # 获取关系数据
    relName = data["rel"]["name"]
    sourceId = data["rel"]["source_uid"]
    targetId = data["rel"]["target_uid"]  #父节点
    # match 父节点
    sql_match_target = "match(p:%s) where p.uid='%s'" %(prj_label,targetId)
    # match 子节点
    sql_match_source = "match(m:%s) where m.uid='%s'" %(prj_label,sourceId)
    # 创建关系语句
    sql_create_ref = "create (p)-[:%s]->(m)"%(relName)
    sql_create_ref = sql_match_target + " " + sql_match_source + " " + sql_create_ref
    print(sql_create_ref)

    graph.run(sql_create_ref)


if __name__ =="__main__":
    # delete_node("PJ4cb80e38554511eb8a32fa163eac98f2","s199465") #s199463,s199458
    #新增节点
    node = {
                "edit_type":"add",
                "obj_type":"node",
                "node":{
                    "uid":"og1",
                    "name":"霍乱10001567888567",
                    "label":"原始词"
                },
                "rel":{
                    "name":"belong_to",
                    "source_uid":"c22",
                    "target_uid":"p11"
                }
            }
    project_id = "PJb9bcf496561a11ebba73fa163eac98f2"

    # creatNode(node,project_id)
    # creatRel(node,project_id)
    delete_node(node,'del_test')

