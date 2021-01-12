# -*- coding: utf-8 -*-
from py2neo import Graph
from pandas import DataFrame
import pandas as pd
import os

# graph = Graph("bolt://120.221.160.106:8002", username="neo4j", password="123456")
graph = Graph("bolt://127.0.0.1:8002", username="neo4j", password="123456")

#复制项目
def copy_prj(prj_old,prj_new,import_dir):
    print("-----开始任务-------")
    pro = get_pro(prj_old) #获取原始项目属性字段
    prj_to_csv(prj_old,pro,os.path.join(import_dir, prj_new)) #导出原始项目到csv
    print("导出csv完成！")
    load_csv(prj_new,pro) #导入csv到新项目 
    print("-----结束任务-------")   
    


#获取原始词、标准词节点所有属性字段
def get_pro(prj_id):
    pro = {}
    pro_ori = set()
    pro_std = set()
    #原始词属性字段
    cql = "match (n:原始词:%s) return distinct keys(n)"%(prj_id)
    result = graph.run(cql).data()
    for res in result:
        pro_ori = pro_ori | set(list(res.values())[0])
    #标准词属性字段
    cql = "match (n:标准词:%s) return distinct keys(n)"%(prj_id)
    result = graph.run(cql).data()
    for res in result:
        pro_std = pro_std | set(list(res.values())[0])   
    #去除非业务字段
    pro_ori = pro_ori - {"in_node","out_node","delete_flag"}
    pro_std = pro_std - {"in_node","out_node","delete_flag"}
    #返回dict
    pro["原始词"] = list(pro_ori)
    pro["标准词"] = list(pro_std)
    return pro

#项目输出到csv
def prj_to_csv(prj_id,pro,out_dir):
    #原始词dataframe
    print("正在读取原始词...")
    pro_ori = pro["原始词"]
    pro_ori_cql = ','.join('n.' + ori for ori in pro_ori )
    cql = "match (n:原始词:%s) return %s "%(prj_id,pro_ori_cql)
    result = graph.run(cql).to_ndarray()
    ori_vocab = DataFrame(result)
    #标准词dataframe
    print("正在读取标准词...")
    pro_std = pro["标准词"]
    pro_std_cql = ','.join('n.' + ori for ori in pro_std )
    cql = "match (n:标准词:%s) return %s  "%(prj_id,pro_std_cql)
    result = graph.run(cql).to_ndarray()
    std_vocab = DataFrame(result)
    #is关系dataframe
    print("正在读取is关系...")
    cql = "match (n:%s)-[r:is]->(m:%s) return n.uid,m.uid "%(prj_id,prj_id)
    result = graph.run(cql).to_ndarray()
    is_rel = DataFrame(result)
    #belong_to关系dataframe
    print("正在读取belong_to关系...")
    cql = "match (n:%s)-[r:belong_to]->(m:%s) return n.uid,m.uid "%(prj_id,prj_id)
    result = graph.run(cql).to_ndarray()
    belong_rel = DataFrame(result)
    #输出到csv
    print("输出结果到csv...")
    ori_vocab.to_csv(os.path.join(out_dir, "ori_vocab.csv"), header=None, index=None)
    std_vocab.to_csv(os.path.join(out_dir, "std_vocab.csv"), header=None, index=None)
    is_rel.to_csv(os.path.join(out_dir, "is_rel.csv"), header=None, index=None)
    belong_rel.to_csv(os.path.join(out_dir, "belong_to_rel.csv"), header=None, index=None)

def load_csv(prj_id,pro):
    print( "开始上传数据！")
    # 创建ori_vocab节点
    ori_head = pro["原始词"]
    ori_pro = ",".join('%s:line[%s]' % (ori_head[i], i) for i in range(len(ori_head)))
    ori_label =  prj_id + ":原始词"
    ori_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line create (m:%s{%s,in_node:"",out_node:"",delete_flag:0})' % (
    "file:///" + prj_id + "/ori_vocab.csv", ori_label, ori_pro)
    print(ori_cypher)
    graph.run(ori_cypher)
    print("创建原始词完成！")
    # 创建std_vocab节点
    std_head = pro["标准词"]
    std_pro = ",".join('%s:line[%s]' % (std_head[i], i) for i in range(len(std_head)))
    std_label = prj_id + ":标准词"
    std_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line create (n:%s{%s,in_node:"",out_node:"",delete_flag:0})' % (
    "file:///" + prj_id + "/std_vocab.csv", std_label, std_pro)
    print(std_cypher)
    graph.run(std_cypher)
    print( "创建标准词完成！")
    # 为所有节点创建 :prj_id(uid) 唯一约束
    cons_uid = 'CREATE CONSTRAINT ON (n:%s) ASSERT n.uid IS UNIQUE' % (prj_id)
    print(cons_uid)
    graph.run(cons_uid)
    print( "创建唯一约束完成！")
    # 为所有节点创建 :prj_id(name) 索引
    index_name = 'create index on :%s(name)' % (prj_id)
    print(index_name)
    graph.run(index_name)
    print( "创建索引完成！")
    # 创建is_rel关系
    is_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line match (m:%s{uid:line[0]}),(n:%s{uid:line[1]}) create (m)-[r:is]->(n)' % (
    "file:///" + prj_id + "/is_rel.csv", prj_id, prj_id)
    print(is_cypher)
    graph.run(is_cypher)
    print( "创建归一关系完成！")
    # 创建belong_rel关系
    belong_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line match (m:%s{uid:line[0]}),(n:%s{uid:line[1]})  create (m)-[r:belong_to]->(n)' % (
    "file:///" + prj_id + "/belong_to_rel.csv", prj_id, prj_id)
    print(belong_cypher)
    graph.run(belong_cypher)
    print( "创建分类关系完成！")
    # 更新相对路径(多路径问题未解决？)
    path_cypher = 'match(n)-[r]->(m) set n.out_node=id(m),m.in_node=id(n)'
    graph.run(path_cypher)
    print( "更新相对路径完成！")



#获取节点dataframe
if __name__ == "__main__":
    copy_prj("PJdc47069e4f3c11ebbbedfa163eac98f2","new_prj_test","/data460/django/neo4j-community-3.5.25/import")

