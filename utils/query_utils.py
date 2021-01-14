# -*- coding: utf-8 -*-

from py2neo import Graph
import copy
import simplejson

# graph = Graph("bolt://120.221.160.106:8002", username="neo4j", password="123456")
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
    print("根据领域，对所有相关项目进行归一查询")
    cards_all = []
    for param in params:
        # print(param)
        cards = query_normalize(param["project_id"],param["project_name"],param["project_fieldcode"],name)
        # print(cards)

        #cards_all.append(copy.deepcopy(cards))
        cards_all = cards_all + cards
    return cards_all

#单一项目归一查询
def query_normalize(prj_label,prj_name,area,name):
    """
    某项目，某领域的归一查询
    """
    cql = "match (n:%s) where n.name='%s' return id(n),labels(n)"%(prj_label,name)
    print(cql)
    result = graph.run(cql).to_ndarray()
    print(result)
    cards = []
    for res in result:
        card = {}
        card["node_id"] = res[0]
        card["node_name"] = name
        card["prj_name"] = prj_name
        card["prj_id"] = prj_label
        card["area"] = area
        card["std_vocab"] = ""
        card["syn_vocab"] = []
        card["graph"] = {}
        cql_tree = ""
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s return id(m),m.name"%(res[0])#自身
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s return m,type(r),n"%(rs[0][0])#归一树
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s return n,type(r),m"%(res[0])#归一树
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

#单一项目归一查询 20200107
def query_normalize_detail(prj_label,prj_name,area,name,node_id):
    """
    某项目，某领域的归一查询
    """
    cql = "match (n:%s) where n.name='%s' and id(n)=%s return id(n),labels(n)"%(prj_label,name,node_id)
    print(cql)
    result = graph.run(cql).to_ndarray()
    print(result)
    cards = []
    for res in result:
        card = {}
        card["node_id"] = res[0]
        card["node_name"] = name
        card["prj_name"] = prj_name
        card["prj_id"] = prj_label
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

#获取节点路径api 20200107
def query_path(arr,node_id,node_name,prj_label):
    arr.append(node_name)
    path = "match (n)-[r]->(m) where id(n)=%s return id(m),m.name" %(node_id)
    result = graph.run(path).to_ndarray()
    if result is not None and len(result) > 0:
        query_path(arr,result[0][0],result[0][1],prj_label)


#通过节点id获取节点信息，选中功能
def select_node(node_id,prj_label):
    """
    项目选中图谱  概念名 路径 标准词 同义词 图谱数据
    选中节点
    :param node_id:
    :param prj_label:
    :return:
    """
    # 查询节点类型
    cql = "match (n:%s) where id(n)=%s return id(n),labels(n),n.name" % (prj_label,node_id)
    result = graph.run(cql).to_ndarray()
    card = {}
    for res in result:
        card["node_id"] = res[0]
        card["node_name"] = res[2]
        card["std_vocab"] = "" # 标准词
        card["syn_vocab"] = [] # 同义词
        card["path"] = [] # 路径
        cql_tree = "" # 同义词
        # 获取同义词和标准词
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s return id(m),m.name" % (res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s return m.name,n.name" % (rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s return n.name,m.name" % (res[0])           
            card["std_vocab"] = res[2]
        rst = graph.run(cql_tree).to_ndarray() # 同义词        
        if "" != cql_tree and len(rst) > 0:
            set1 = set(rr[0] for rr in rst)
            set2 = set1 | set(rr[1] for rr in rst)
            card["syn_vocab"] = list(set2)
            card["syn_vocab"].remove(res[2])
        #节点路径
        arr = []
        query_path(arr,node_id,res[2],prj_label)
        arr.reverse()
        card["path"] = arr
    return card

#获取节点与之相连的树
def get_node_tree(node_id,prj_label):
    tree = {}
    tree_in = {}
    tree_out = {}
    cql_tree_in = "match (n)-[r]->(m) where id(m)=%s return m,type(r),n" %(node_id)
    rs_in = graph.run(cql_tree_in).to_ndarray()
    if len(rs_in) > 0:
        tree_in = select_tree_info(rs_in, prj_label)
    cql_tree_out = "match (n)-[r]->(m) where id(n)=%s return m,type(r),n" %(node_id)
    rs_out = graph.run(cql_tree_out).to_ndarray()
    if len(rs_out) > 0:
        tree_out = select_tree_info(rs_out, prj_label)
    tree["nodes"] = drop_dupls(tree_in["nodes"] + tree_out["nodes"])
    tree["rels"] = drop_dupls(tree_in["rels"] + tree_out["rels"])
    return tree

#聚焦功能
def focus_node(node_id,prj_label):
    node_info = select_node(node_id,prj_label)
    node_tree = get_node_tree(node_id,prj_label)
    return dict(node_info, **node_tree)

#项目谱图查询功能
def query_node(node_name,prj_label):
    node_info = select_node_name(node_name, prj_label)
    return node_info

#根据查询结果返回树结构信息 20210107
def select_tree_info(result,prj_label):
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

#通过节点名称获取节点信息
def select_node_name(name,prj_label):
    cql = "match (n:%s) where n.name='%s' return id(n),labels(n),n" % (prj_label, name)
    result = graph.run(cql).to_ndarray()
    cards = []
    for res in result:
        card = {}
        card["node_id"] = res[0]
        card["node_name"] = name
        card["std_vocab"] = ""  # 标准词
        card["syn_vocab"] = []  # 同义词
        card["path"] = []  # 路径
        card["properties"] = {} # 属性
        # 通过节点获取属性
        properties = {}
        for k, v in res[2].items():  # 遍历属性，排除非业务字段
            if k not in ['uid', 'delete_flag', 'in_node', 'out_node']:
                properties[k] = v
        card["properties"] = properties
        cql_tree = ""  # 同义词
        # 获取同义词和标准词
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s return id(m),m.name" % (res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s return m.name,n.name" % (rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s return n.name,m.name" % (res[0])
            card["std_vocab"] = name
        rst = graph.run(cql_tree).to_ndarray()  # 同义词
        if "" != cql_tree and len(rst) > 0:
            set1 = set(rr[0] for rr in rst)
            set2 = set1 | set(rr[1] for rr in rst)
            card["syn_vocab"] = list(set2)
            card["syn_vocab"].remove(res[2])
        # 节点路径
        arr = []
        query_path(arr, res[0], name, prj_label)
        arr.reverse()
        card["path"] = arr
        cards.append(copy.deepcopy(card))
    return cards

#获取节点名称与之相连的树
def get_node_tree_name(name,prj_label):
    tree = {}
    tree_in = {}
    tree_out = {}
    cql_tree_in = "match (n:%s)-[r]->(m) where m.name='%s' return m,type(r),n" %(prj_label,name)
    rs_in = graph.run(cql_tree_in).to_ndarray()
    if len(rs_in) > 0:
        tree_in = select_tree_info(rs_in, prj_label)
    cql_tree_out = "match (n:%s)-[r]->(m) where n.name='%s' return m,type(r),n" %(prj_label,name)
    rs_out = graph.run(cql_tree_out).to_ndarray()
    if len(rs_out) > 0:
        tree_out = select_tree_info(rs_out, prj_label)
    tree["nodes"] = drop_dupls(tree_in["nodes"] + tree_out["nodes"])
    tree["rels"] = drop_dupls(tree_in["rels"] + tree_out["rels"])
    return tree



if __name__ == "__main__":

    # 归一查询api  项目标签查询 名称属性查询
    # trees = query_normalize('test','测试项目','测试领域','test')
    # print(trees)
    # print(type(trees))

    # 应用诡异查询
    # arr = [
    #         {
    #             "project_id":"PJ7f6fd5924ef911eb8817fa163eac98f2",
    #             "project_name":"PJ7f6fd5924ef911eb8817fa163eac98f2",
    #             "project_fieldcode":"kangjun"
    #         }
    #     ]
    # trees = query_normalize_all(arr, '由霍乱弧菌埃尔托型引起的霍乱6')
    #
    #
    # trees = simplejson.dumps(trees,ensure_ascii=False)
    # print(trees)
    #node = select_node(8540670,'PJ1dacfe724fc411ebb771fa163eac98f2')
    # tree = focus_node(8540670,'PJ1dacfe724fc411ebb771fa163eac98f2')
    # tree = query_node('某些传染病和寄生虫病9740','PJ1dacfe724fc411ebb771fa163eac98f2')
    # trees = simplejson.dumps(tree,ensure_ascii=False)
    # print(trees)
    # aList = [123, 'xyz', 'zara', 'abc', 'xyz']
    #
    # aList.reverse()
    # print("List : ", aList)

    arr = []

    arr.reverse()
    print(arr)

    # query_path(arr,8360647,"test",'PJ1dacfe724fc411ebb771fa163eac98f2')
    # print(arr)

