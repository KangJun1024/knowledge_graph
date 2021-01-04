# -*- coding: utf-8 -*-

from py2neo import Graph
import copy
import simplejson

graph = Graph("bolt://127.0.0.1:8002", username="neo4j", password="123456")

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
    #返回树信息
    tree = {}
    if len(result) > 0:
        tree = tree_info(result,prj_label)
    return tree

#根据查询结果返回树结构信息
def tree_info(result,prj_label):
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
            rel_info["source"] = str(res[r+1].identity)
            rel_info["target"] = str(res[r-1].identity)
            rels.append(copy.deepcopy(rel_info))
        #获取节点
        for i in n_index:
            node_info = {}
            node_info["id"] = res[i].identity
            node_info["labels"] = list(res[i].labels)
            node_info["labels"].remove(prj_label)
            properties = {}
            for k,v in res[i].items(): #遍历属性，排除非业务字段
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


#根据领域，对所有相关项目进行归一查询
def query_normalize_all(params:[],name:str):
    """
    需先根据领域，通过mysql项目表，组装params参数，结构如下
    [
        {
            "prj_label":"P10001",
            "prj_name":"测试项目",
            "area":"测试领域"
        }
        {
            ...
        }
    ]
    """
    cards_all = []
    for param in params:
        cards = query_normalize(param["prj_label"],param["prj_name"],param["area"],name)
        #cards_all.append(copy.deepcopy(cards))
        cards_all = cards_all + cards
    return cards_all

#单一项目归一查询
def query_normalize(prj_label,prj_name,area,name):
    """
    某项目，某领域的归一查询
    """
    cql = "match (n:%s) where n.name='%s' return id(n),labels(n)"%(prj_label,name)
    result = graph.run(cql).to_ndarray()
    cards = []
    for res in result:
        card = {}
        card["node_id"] = res[0]
        card["node_name"] = name
        card["prj_name"] = prj_name
        card["area"] = area
        card["std_vocab"] = ""
        card["syn_vocab"] = []
        card["graph"] = {}
        cql_tree = ""
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s return id(m),m.name"%(res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s return m,type(r),n"%(rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s return n,type(r),m"%(res[0])
            card["std_vocab"] = name
        rst = graph.run(cql_tree).to_ndarray()
        if "" != cql_tree and len(rst) > 0:
            tree = tree_info(rst,prj_label)#返回归一树信息
            card["syn_vocab"] = [tr["name"] for tr in tree["nodes"]]
            card["syn_vocab"].remove(name)
            card["graph"] = tree
        else:
            tree = {}#按树结构只返回一个节点
            tree["nodes"] = [node_info(res[0],prj_label)]
            tree["rels"] = []
            card["syn_vocab"] = []
            card["graph"] = tree
        cards.append(copy.deepcopy(card))
    return cards

#通过id返回节点信息
def node_info(n_id,prj_label):
    cql = "match (n) where id(n)=%s return n"%(n_id)
    result = graph.run(cql).to_ndarray()
    nd = result[0][0]
    node_info = {}
    node_info["id"] = n_id
    node_info["labels"] = list(nd.labels)
    node_info["labels"].remove(prj_label)
    properties = {}
    for k,v in nd.items(): #遍历属性，排除非业务字段
        if k == "name":
            node_info[k] = v
        elif k not in ['uid','delete_flag','in_node','out_node']:
            properties[k] = v
    node_info["properties"] = properties
    return node_info





if __name__ == "__main__":
    # 输入参数
    # handler = SelectVocab()
    # arg = handler.getArguments()
    # handler.select_vocab(arg.name,arg.labels,arg.where,arg.outnode,arg.outformat,arg.outsize)
    # handler.select_vocab("恰里畸形",None,None,"brother",None) #测试



    # arr = ['P10001']
    # # # 获取概念或三元组数量  type:0概念数  1三元组数  list: 项目标签 空数组查询统计数据
    # print(get_nd_rel_ct(arr,0))


    # 初始化三层数据 项目标签查询
    # trees = get_prj_kg('P10001')
    # print(get_prj_kg('P10001'))


    # 归一查询api  项目标签查询 名称属性查询
    # trees = query_normalize('test','测试项目','测试领域','test')
    # print(trees)
    # print(type(trees))

    # 应用诡异查询
    arr = [
            {
                "prj_label":"P10001",
                "prj_name":"测试项目",
                "area":"测试领域"
            },
            {
                "prj_label":"P10001",
                "prj_name":"测试项目2",
                "area":"测试领域2"
            }
        ]
    trees = query_normalize_all(arr, '由霍乱弧菌埃尔托型引起的霍乱6')


    trees = simplejson.dumps(trees,ensure_ascii=False)
    print(trees)