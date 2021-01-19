# -*- coding: utf-8 -*-
from py2neo import Graph
from pandas import DataFrame
import pandas as pd

graph = Graph("bolt://120.221.160.106:8002", username="neo4j", password="123456")


#删除节点及其子树
def delete_node(prj_label,node_uid):    
    cql = "match(n:%s) where n.uid = '%s' return id(n)" %(prj_label,node_uid)
    result = graph.run(cql).to_ndarray()  #通过uid获取id
    if len(result) > 0:
        input_id = result[0][0]
        del_nodes = query_del_nodes(input_id) #获取需删除的树所有id
        cql = "match(n:%s) where id(n) in %s detach delete n" %(prj_label,str(del_nodes))
        graph.run(cql) #删除节点

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
        cql = "match(n)<-[r]-(m) where id(n)=%s return id(m)" %(input_id)
        result = graph.run(cql).to_ndarray() #二维数组        
        for r in result:
            query_children_tree(r[0],tree)

#查找递归树中有外部父节点的节点
def query_multi_parent(tree):
    arr = []
    for t in tree:
        cql = "match(n)-[r]->(m) where id(n)=%s return id(m)" %(t)
        result = graph.run(cql).to_ndarray() #二维数组  
        for r in result:
            if r[0] not in tree: #判断是否有外部父节点
                arr.append(t)
                break
    return arr        


if __name__ =="__main__":
    delete_node("PJ4cb80e38554511eb8a32fa163eac98f2","s199465") #s199463,s199458




