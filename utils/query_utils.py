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
        cql = "match (n%s) where n.delete_flag = 0 return count(n)"%(labels_sql)
    #三元组数量
    if  type is not None and 1 == type:
        cql = "match (n%s)-[r]->(m) where n.delete_flag = 0 and m.delete_flag = 0 return count(n)"%(labels_sql)
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
    cql = "match (n:%s) where n.class = '顶级节点' and n.delete_flag = 0 return n limit 1"%(prj_label) #直接取顶级节点
    result = graph.run(cql).to_ndarray()
    if len(result) == 0: #无顶级节点标识，取随机一棵树的顶点
        cql = "match (n:%s) with size((n)-[]->()) as out,size((n)<-[]-()) as in, n where out = 0 and in > 0 return n ORDER BY RAND() limit 1"%(prj_label)
        result = graph.run(cql).to_ndarray()
    if len(result) > 0:
        top_id = result[0][0].identity
    else:
        return {}
    #由顶点向下搜索树
    cql = "match(n:%s)<-[r1]-(p)<-[r2]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return n,type(r1),p,type(r2),m limit 50"%(prj_label,top_id) #取三层结构
    result = graph.run(cql).to_ndarray()
    if len(result) == 0: #无三层结构，取两层结构
        cql = "match(n:%s)<-[r1]-(p) where id(n)=%s and n.delete_flag = 0 and p.delete_flag = 0 return n,type(r1),p limit 100"%(prj_label,top_id) #取两层结构
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
            rel_info["type"] = res[r]
            rel_info["name"] = getRefName(res[r])
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
                elif k  not in ['delete_flag','in_node','out_node']:
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
    cql = "match (n:%s) where n.name='%s' and n.delete_flag = 0 return id(n),labels(n)"%(prj_label,name)
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
            cql = "match (n)-[r:is]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m),m.name"%(res[0])#自身
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n"%(rs[0][0])#归一树
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return n,type(r),m"%(res[0])#归一树
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
    cql = "match (n) where id(n)=%s and n.delete_flag = 0 return n"%(n_id)
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
        elif k not in ['delete_flag','in_node','out_node']:
            properties[k] = v
    node_info["properties"] = properties
    return node_info

#通过关系类型code获取关系类型名称
def getRefName(type):
    if "belong_to" == type:
        return "属于"
    else:
        return "标准化为"
#单一项目归一查询 20200107
def query_normalize_detail(prj_label,prj_name,area,name,node_id):
    """
    某项目，某领域的归一查询
    """
    cql = "match (n:%s) where n.name='%s' and id(n)=%s and n.delete_flag = 0 return id(n),labels(n),n"%(prj_label,name,node_id)
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
        card["properties"] = {}  # 属性
        # 通过节点获取属性
        properties = {}
        for k, v in res[2].items():  # 遍历属性，排除非业务字段
            if k not in ['delete_flag', 'in_node', 'out_node']:
                properties[k] = v
        card["properties"] = properties
        cql_tree = ""
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m),m.name"%(res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n"%(rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return n,type(r),m"%(res[0])
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
def query_path(arr,node_id,node_name,prj_label,temp_id):
    arr.append(node_name)
    path = "match (n:%s)-[r]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m),m.name" %(prj_label,node_id)
    print(path)
    result = graph.run(path).to_ndarray()
    if result is not None and len(result) > 0 and str(temp_id) != result[0][0]:
        #判断成环的情况
        query_path(arr,result[0][0],result[0][1],prj_label,temp_id)


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
    cql = "match (n:%s) where id(n)=%s and n.delete_flag = 0 return id(n),labels(n),n.name,n" % (prj_label,node_id)
    print(cql)
    result = graph.run(cql).to_ndarray()
    card = {}
    for res in result:
        card["node_id"] = res[0]
        card["node_name"] = res[2]
        card["std_vocab"] = "" # 标准词
        card["syn_vocab"] = [] # 同义词
        card["path"] = [] # 路径
        card["properties"] = {}  # 属性
        # 通过节点获取属性
        properties = {}
        for k, v in res[3].items():  # 遍历属性，排除非业务字段
            if k not in ['delete_flag', 'in_node', 'out_node']:
                properties[k] = v
        card["properties"] = properties
        cql_tree = "" # 同义词
        # 获取同义词和标准词
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m),m.name" % (res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m.name,n.name" % (rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return n.name,m.name" % (res[0])
            card["std_vocab"] = res[2]
        rst = graph.run(cql_tree).to_ndarray() # 同义词
        print(cql_tree)
        if "" != cql_tree and len(rst) > 0:
            set1 = set(rr[0] for rr in rst)
            set2 = set1 | set(rr[1] for rr in rst)
            card["syn_vocab"] = list(set2)
            card["syn_vocab"].remove(res[2])
        #节点路径
        arr = []
        query_path(arr,node_id,res[2],prj_label,node_id)
        arr.reverse()
        card["path"] = arr
    return card

#获取节点与之相连的树
def get_node_tree(node_id,prj_label):
    tree = {}
    tree_in = {}
    tree_out = {}
    cql_tree_in = "match (n)-[r]->(m) where id(m)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n" %(node_id)
    rs_in = graph.run(cql_tree_in).to_ndarray()
    if len(rs_in) > 0:
        tree_in = select_tree_info(rs_in, prj_label)
    cql_tree_out = "match (n)-[r]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n" %(node_id)
    rs_out = graph.run(cql_tree_out).to_ndarray()
    if len(rs_out) > 0:
        tree_out = select_tree_info(rs_out, prj_label)
    if not tree_in:
        tree_in["nodes"] = []
        tree_in["rels"] = []
    if not tree_out:
        tree_out["nodes"] = []
        tree_out["rels"] = []
    print(tree_in)
    print(tree_out)
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
            rel_info["type"] = res[r]
            rel_info["name"] = getRefName(res[r])
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
                elif k  not in ['delete_flag','in_node','out_node']:
                    properties[k] = v
            node_info["properties"] = properties
            nodes.append(copy.deepcopy(node_info))
    tree["nodes"] = drop_dupls(nodes)
    tree["rels"] = drop_dupls(rels)
    return tree

#通过节点名称获取节点信息
def select_node_name(name,prj_label):
    cql = "match (n:%s) where n.name='%s' and n.delete_flag = 0 return id(n),labels(n),n" % (prj_label, name)
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
            if k not in ['delete_flag', 'in_node', 'out_node']:
                properties[k] = v
        card["properties"] = properties
        cql_tree = ""  # 同义词
        # 获取同义词和标准词
        if "原始词" in res[1]:
            cql = "match (n)-[r:is]->(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return id(m),m.name" % (res[0])
            rs = graph.run(cql).to_ndarray()
            if len(rs) > 0:
                cql_tree = "match (n)-[r:is]->(m) where id(m)=%s and n.delete_flag = 0 and m.delete_flag = 0 return m.name,n.name" % (rs[0][0])
                card["std_vocab"] = str(rs[0][1])
        elif "标准词" in res[1]:
            cql_tree = "match (n)<-[r:is]-(m) where id(n)=%s and n.delete_flag = 0 and m.delete_flag = 0 return n.name,m.name" % (res[0])
            card["std_vocab"] = name
        rst = graph.run(cql_tree).to_ndarray()  # 同义词
        print(cql_tree)
        if "" != cql_tree and len(rst) > 0:
            set1 = set(rr[0] for rr in rst)
            set2 = set1 | set(rr[1] for rr in rst)
            card["syn_vocab"] = list(set2)
            card["syn_vocab"].remove(name)
        # 节点路径
        arr = []
        query_path(arr, res[0], name, prj_label,res[0])
        arr.reverse()
        card["path"] = arr
        cards.append(copy.deepcopy(card))
    return cards

#获取节点名称与之相连的树
def get_node_tree_name(name,prj_label):
    tree = {}
    tree_in = {}
    tree_out = {}
    cql_tree_in = "match (n:%s)-[r]->(m) where m.name='%s' and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n" %(prj_label,name)
    rs_in = graph.run(cql_tree_in).to_ndarray()
    if len(rs_in) > 0:
        tree_in = select_tree_info(rs_in, prj_label)
    cql_tree_out = "match (n:%s)-[r]->(m) where n.name='%s' and n.delete_flag = 0 and m.delete_flag = 0 return m,type(r),n" %(prj_label,name)
    rs_out = graph.run(cql_tree_out).to_ndarray()
    if len(rs_out) > 0:
        tree_out = select_tree_info(rs_out, prj_label)
    tree["nodes"] = drop_dupls(tree_in["nodes"] + tree_out["nodes"])
    tree["rels"] = drop_dupls(tree_in["rels"] + tree_out["rels"])
    return tree

import base64

def convert_base64_src_to_img_file(src=None):
    test_src = 'data:image/png;base64,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'
    if src is None:
        src = test_src
    if (len(src) % 3 == 1):
        src += "="
    elif (len(src) % 3 == 2):
        src += "=="
    print(src)
    data = src.split('base64,')[-1]
    mime = src.split('data:image/')[-1].split(';base64')[0]
    print(data)
    image_data = base64.b64decode(data)
    file_name = "test"
    file_path = 'D:\{}.{}'.format(file_name, mime)
    with open(file_path, 'wb') as f:
        f.write(image_data)

if __name__ == "__main__":
    convert_base64_src_to_img_file()

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
    # tree = focus_node(13088347,'PJ3fcccf80556611ebac42fa163eac98f2')
    # tree = query_node('某些传染病和寄生虫病9740','PJ1dacfe724fc411ebb771fa163eac98f2')
    # trees = simplejson.dumps(tree,ensure_ascii=False)
    # print(trees)
    # aList = [123, 'xyz', 'zara', 'abc', 'xyz']
    #
    # aList.reverse()
    # print("List : ", aList)

    arr = []
    #
    # arr.reverse()
    # print(arr)

    query_path(arr,12920043,"肠道传染病9869",'PJ5d54ef78556211ebb65ffa163eac98f2',12920043)
    # print(arr)

