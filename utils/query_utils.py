# -*- coding: utf-8 -*-

from py2neo import Graph
import copy
import json,simplejson

graph = Graph("bolt://120.221.160.120:19442", username="neo4j", password="123456")

#获取概念或三元组数量
def get_nd_rel_ct(labels:list,type:int):
    """
    labels: 标签数组（and关系）
    type: 0:概念数 1:三元组数
    """
    #labels组装
    labels_sql = ""
    cql = ""
    ct = 0
    if labels is not None and len(labels) > 0:
        labels_sql = ':' + ':'.join(str(label) for label in labels)
    #概念数量
    if  type is not None and 0 == type:
        cql = "match (n%s) return count(n)"%(labels_sql)
    #三元组数量
    if  type is not None and 1 == type:
        cql = "match (n%s)-[r]->(m) return count(n)"%(labels_sql)
    if "" != cql:
        print(cql)
        ct = list(graph.run(cql).data()[0].values())[0]
    return int(ct)

#获取初始化项目图谱
def get_prj_kg(prj_label:str):
    """
    搜索顶级向下三层，返回节点详细信息以及关系,格式如下
    {
    "nodes": [
        {
            "id": 885938,
            "labels": ["P10001","标准词"],
            "name": "疾病名称",
            "properties": {"class": "顶级节点"}
        }
    ],
    "rels": [
        {
            "name": "belong_to",
            "source": 885937,
            "target": 885938
        }
    ]
    }
    其中，以下为通用属性，非业务字段，不返回
    ['uid','delete_flag','in_node','out_node']
    """
    #顶级节点选取
    cql = "match (n:%s) where n.class = '顶级节点' return n limit 1"%(prj_label) #直接取顶级节点
    result = graph.run(cql).to_ndarray()
    if len(result) == 0: #无顶级节点标识，取随机一棵树的顶点
        cql = "match (n:%s) with size((n)-[]->()) as out,size((n)<-[]-()) as in, n where out = 0 and in > 0 return n ORDER BY RAND() limit 1"%(prj_label)
        result = graph.run(cql).to_ndarray()
    if len(result) > 0:
        top_id = result[0][0].identity
    else:
        return {}
    #由顶点向下搜索树
    cql = "match(n:%s)<-[r1]-(p)<-[r2]-(m) where id(n)=%s return n,type(r1),p,type(r2),m limit 50"%(prj_label,top_id) #取三层结构
    result = graph.run(cql).to_ndarray()
    if len(result) == 0: #无三层结构，取两层结构
        cql = "match(n:%s)<-[r1]-(p) where id(n)=%s return n,type(r1),p limit 100"%(prj_label,top_id) #取两层结构
        result = graph.run(cql).to_ndarray()
    if len(result[0]) == 5: #三层结构
        r_index = [1,3]
        n_index = [0,2,4]
    elif len(result[0]) == 3: #两层结构
        r_index = [1]
        n_index = [0,2]
    tree = {}
    nodes = []
    rels = []
    for res in result:
        #获取关系
        for r in r_index:
            rel_info = {}
            rel_info["name"] = res[r]
            rel_info["source"] = res[r+1].identity
            rel_info["target"] = res[r-1].identity
            rels.append(copy.deepcopy(rel_info))
        #获取节点
        for i in n_index:
            node_info = {}
            node_info["id"] = res[i].identity                     
            node_info["labels"] = list(res[i].labels)
            node_info["labels"].remove(prj_label)
            properties = {}  
            for k,v in res[i].items():                 
                if k == "name":
                    node_info[k] = v
                elif k  not in ['uid','delete_flag','in_node','out_node']:
                    properties[k] = v 
            node_info["properties"] = properties
            nodes.append(copy.deepcopy(node_info))
    tree["nodes"] = drop_dupls(nodes)
    tree["rels"] = drop_dupls(rels)
    return tree
    
# list去重
def drop_dupls(arr):
    new_arr = []
    for a in arr:
        if a not in new_arr:
            new_arr.append(a)
    return new_arr

#归一查询
def query_normalize_by_name(prj_label,name):
    cql = "match (n:%s) where n.name='%s' return id(n)"%(prj_label,name)
    result = graph.run(cql).to_ndarray()
    trees = {}
    for res in result:
        tree = query_normalize_by_id(res[0])
        trees[res[0]] = tree
    return trees

#通过id查询包含父、子节点的三层结构树
def query_normalize_by_id(n_id):
    cql1 = "match (n1)<-[r1]-(m1) where id(n1)=%s return n1,type(r1),m1"%(n_id)    
    result1 = graph.run(cql1).to_ndarray()
    cql2 = "match (n2)-[r2]->(m2) where id(n2)=%s return m2,type(r2),n2"%(n_id) 
    result2 = graph.run(cql2).to_ndarray()
    result = []
    for res1 in result1:
        result.append(res1)
    for res2 in result2:
        result.append(res2)
    tree = {}
    nodes = []
    rels = []
    for res in result:
        #获取关系
        for r in [1]:
            rel_info = {}
            rel_info["name"] = res[r]
            rel_info["source"] = res[r+1].identity
            rel_info["target"] = res[r-1].identity
            rels.append(copy.deepcopy(rel_info))
        #获取节点
        for i in [0,2]:
            node_info = {}
            node_info["id"] = res[i].identity                     
            node_info["labels"] = list(res[i].labels)
            #node_info["labels"].remove(prj_label)
            properties = {}  
            for k,v in res[i].items():                 
                if k == "name":
                    node_info[k] = v
                elif k  not in ['uid','delete_flag','in_node','out_node']:
                    properties[k] = v 
            node_info["properties"] = properties
            nodes.append(copy.deepcopy(node_info))
    tree["nodes"] = drop_dupls(nodes)
    tree["rels"] = drop_dupls(rels)

    return tree




                                
if __name__ == "__main__":
    # 输入参数
    # handler = SelectVocab()
    # arg = handler.getArguments()
    # handler.select_vocab(arg.name,arg.labels,arg.where,arg.outnode,arg.outformat,arg.outsize)
    # handler.select_vocab("恰里畸形",None,None,"brother",None) #测试



    # arr = ['P10001']
    # # 获取概念或三元组数量  type:0概念数  1三元组数  list: 项目标签 空数组查询统计数据
    # print(get_nd_rel_ct([],1))


    # 初始化三层数据 项目标签查询
    trees = get_prj_kg('P10001')
    print(get_prj_kg('P10001'))


    # 归一查询api  项目标签查询 名称属性查询
    # trees = query_normalize_by_name('P10001','霍乱弧菌引起的霍乱6')
    # print(trees)
    # print(type(trees))
    trees = simplejson.dumps(trees,ensure_ascii=False)
    print(trees)