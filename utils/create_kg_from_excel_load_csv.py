# # -*- coding: utf-8 -*-
# from py2neo import Graph
# from pandas import Series, DataFrame
# import pandas as pd
# import os
# import re
# import time
#
# class CreateGraph:
#     def __init__(self):
#         self.graph = Graph("bolt://120.221.160.120:19442", username="neo4j", password="123456")
#         # self.head = {
#         #     '原始词': ['原始词[name]'],
#         #     '标准词': ['标准词[name]', '标准词[class]', '标准词[code]', '标准词[code_add]']
#         # }
#         self.head = {}
#         self.ori_vocab = DataFrame()
#         self.std_vocab = DataFrame()
#         self.is_rel = DataFrame()
#         self.belong_rel = DataFrame()
#
#     def neo4j_load_csv(self,labels):
#         print(self.get_localtime() + "开始上传数据！")
#         #创建ori_vocab节点
#         ori_head = self.head["原始词"]
#         ori_pro = ",".join('%s:line[%s]'%(re.findall("[[](.*?)[]]",ori_head[i])[0],i + 1) for i in range(len(ori_head)))
#         ori_label = ":".join(l for l in labels.split(",") + ["原始词"])
#         ori_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line create (m:%s{uid:line[0],%s,in_node:"",out_node:"",delete_flag:0})'%("file:///" + labels + "/ori_vocab.csv",ori_label,ori_pro)
#         print(ori_cypher)
#         self.graph.run(ori_cypher)
#         print(self.get_localtime() + "创建原始词完成！")
#         #创建std_vocab节点
#         std_head = self.head["标准词"]
#         std_pro = ",".join('%s:line[%s]'%(re.findall("[[](.*?)[]]",std_head[i])[0],i + 1) for i in range(len(std_head)))
#         std_label = ":".join(l for l in labels.split(",") + ["标准词"])
#         std_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line create (n:%s{uid:line[0],%s,in_node:"",out_node:"",delete_flag:0})'%("file:///" + labels + "/std_vocab.csv",std_label,std_pro)
#         print(std_cypher)
#         self.graph.run(std_cypher)
#         print(self.get_localtime() + "创建标准词完成！")
#         #为所有节点创建 :labels(uid) 唯一约束
#         cons_uid = 'CREATE CONSTRAINT ON (n:%s) ASSERT n.uid IS UNIQUE'%(labels)
#         print(cons_uid)
#         self.graph.run(cons_uid)
#         print(self.get_localtime() + "创建唯一约束完成！")
#         #为所有节点创建 :labels(name) 索引
#         index_name = 'create index on :%s(name)'%(labels)
#         print(index_name)
#         self.graph.run(index_name)
#         print(self.get_localtime() + "创建索引完成！")
#         #创建is_rel关系
#         is_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line match (m:%s{uid:line[0]}),(n:%s{uid:line[1]}) create (m)-[r:is]->(n)'%("file:///" + labels + "/is_rel.csv",labels,labels)
#         print(is_cypher)
#         self.graph.run(is_cypher)
#         print(self.get_localtime() + "创建归一关系完成！")
#         #创建belong_rel关系
#         belong_cypher = 'USING PERIODIC COMMIT 5000 LOAD CSV FROM "%s" AS line match (m:%s{uid:line[0]}),(n:%s{uid:line[1]})  create (m)-[r:belong_to]->(n)'%("file:///" + labels + "/belong_to_rel.csv",labels,labels)
#         print(belong_cypher)
#         self.graph.run(belong_cypher)
#         print(self.get_localtime() + "创建分类关系完成！")
#         #更新相对路径(多路径问题未解决？)
#         path_cypher = 'match(n)-[r]->(m) set n.out_node=id(m),m.in_node=id(n)'
#         self.graph.run(path_cypher)
#         print(self.get_localtime() + "更新相对路径完成！")
#
#
#     def read_excel_save_csv(self,excel_path):
#         """
#         读取excel内容，输出csv到同目录
#         excel路径最好放在 $NEO4J_HOME/import/$prj/
#         """
#         reader = pd.ExcelFile(excel_path)
#         for name in reader.sheet_names:
#             df = pd.read_excel(reader,sheet_name = name)
#             self.sheet_into_df(df)
#         self.clean_df()
#         #输出到csv
#         dir = os.path.dirname(excel_path)
#         self.ori_vocab.to_csv(os.path.join(dir,"ori_vocab.csv"),header=None,index=None)
#         self.std_vocab.to_csv(os.path.join(dir,"std_vocab.csv"),header=None,index=None)
#         self.is_rel.to_csv(os.path.join(dir,"is_rel.csv"),header=None,index=None)
#         self.belong_rel.to_csv(os.path.join(dir,"belong_to_rel.csv"),header=None,index=None)
#
#
#     def clean_df(self):
#         """
#         清洗dataframe，并添加索引
#         """
#         #去重，并替换None值与特殊字符
#         self.ori_vocab = self.ori_vocab.drop_duplicates().fillna('')#.replace("\\","\\\\").replace("'","\\'")
#         self.std_vocab = self.std_vocab.drop_duplicates().fillna('')#.replace("\\","\\\\").replace("'","\\'")
#         self.is_rel = self.is_rel.drop_duplicates().fillna('')#.replace("\\","\\\\").replace("'","\\'")
#         self.belong_rel = self.belong_rel.drop_duplicates().fillna('')#.replace("\\","\\\\").replace("'","\\'")
#         #过滤，去除name为“—”、“”所在的行
#         self.ori_vocab = self.ori_vocab[~self.ori_vocab["原始词[name]"].isin(["—",""])]
#         self.std_vocab = self.std_vocab[~self.std_vocab["标准词[name]"].isin(["—",""])]
#         self.is_rel = self.is_rel[~self.is_rel["原始词[name]"].isin(["—",""])]
#         self.is_rel = self.is_rel[~self.is_rel["标准词[name]"].isin(["—",""])]
#         self.belong_rel = self.belong_rel[~self.belong_rel["标准词[name]"].isin(["—",""])]
#         self.belong_rel = self.belong_rel[~self.belong_rel["标准词[name]_1"].isin(["—",""])]
#         #改造ori_vocab、std_vocab，添加全字段值作为uniq索引，添加uid列
#         self.ori_vocab["uniq"] = '' #新建列，用于拼接所有列成唯一值
#         self.ori_vocab = self.ori_vocab.astype(str) #整个df设置为str
#         for col in self.head["原始词"]: #全字段值相加
#             self.ori_vocab["uniq"] = self.ori_vocab["uniq"] + self.ori_vocab[col]
#         self.ori_vocab = self.ori_vocab.reset_index(drop = True) #重置行索引
#         self.ori_vocab = self.ori_vocab.reset_index(drop = False) #行索引作为列值
#         self.ori_vocab = self.ori_vocab.astype(str) #设置为str
#         self.ori_vocab['index'] = 'o' + self.ori_vocab['index'] #index拼接，入库后区分节点id
#         self.ori_vocab = self.ori_vocab.set_index(["uniq"]) #uniq作为行索引
#         self.std_vocab["uniq"] = ''
#         self.std_vocab = self.std_vocab.astype(str)
#         for col in self.head["标准词"]:
#             self.std_vocab["uniq"] = self.std_vocab["uniq"] + self.std_vocab[col]
#         self.std_vocab = self.std_vocab.reset_index(drop = True)
#         self.std_vocab = self.std_vocab.reset_index(drop = False)
#         self.std_vocab = self.std_vocab.astype(str)
#         self.std_vocab['index'] = 's' + self.std_vocab['index']
#         self.std_vocab = self.std_vocab.set_index(["uniq"])
#         #改造is_rel、belong_rel，将关系存入
#         self.is_rel['uniq_ori'] = ''
#         self.is_rel['uniq_std'] = ''
#         for col in self.head["原始词"]: #拼接所有列成唯一值
#             self.is_rel['uniq_ori'] = self.is_rel['uniq_ori'] + self.is_rel[col]
#         for col in self.head["标准词"]: #拼接所有列成唯一值
#             self.is_rel['uniq_std'] = self.is_rel['uniq_std'] + self.is_rel[col]
#         self.is_rel = self.is_rel[['uniq_ori','uniq_std']]
#         self.is_rel = pd.merge(left=self.is_rel,right=self.ori_vocab,how='left',left_on='uniq_ori',right_on='uniq') #left join取得原始词uid
#         self.is_rel = self.is_rel[['index','uniq_std']]
#         self.is_rel = self.is_rel.rename(columns={"index":"uniq_ori"})
#         self.is_rel = pd.merge(left=self.is_rel,right=self.std_vocab,how='left',left_on='uniq_std',right_on='uniq') #left join取得标准词uid
#         self.is_rel = self.is_rel[['uniq_ori','index']]
#         self.is_rel = self.is_rel.rename(columns={"index":"uniq_std"})
#         #改造is_rel、belong_rel，将关系存入
#         self.belong_rel['uniq_std'] = ''
#         self.belong_rel['uniq_std_1'] = ''
#         for col in self.head["标准词"]:
#             self.belong_rel['uniq_std'] = self.belong_rel['uniq_std'] + self.belong_rel[col]
#             self.belong_rel['uniq_std_1'] = self.belong_rel['uniq_std_1'] + self.belong_rel[col + '_1']
#         self.belong_rel = self.belong_rel[['uniq_std','uniq_std_1']]
#         self.belong_rel = pd.merge(left=self.belong_rel,right=self.std_vocab,how='left',left_on='uniq_std',right_on='uniq') #left join取得原始词uid
#         self.belong_rel = self.belong_rel[['index','uniq_std_1']]
#         self.belong_rel = self.belong_rel.rename(columns={"index":"uniq_std"})
#         self.belong_rel = pd.merge(left=self.belong_rel,right=self.std_vocab,how='left',left_on='uniq_std_1',right_on='uniq') #left join取得标准词uid
#         self.belong_rel = self.belong_rel[['uniq_std','index']]
#         self.belong_rel = self.belong_rel.rename(columns={"index":"uniq_std_1"})
#
#     def sheet_into_df(self,df):
#         """
#         将sheet的数据内容，输出到各个dataframe
#         """
#         head_index = self.head_index(df)
#         head_col = self.head_col(df)
#         if len(self.head) == 0 or len(self.head["原始词"]) == 0 or len(self.head["标准词"]) == 0:
#             self.head = head_col #记录原始词标准词所有属性列
#         for o in head_index["原始词"]:
#             #原始词
#             df_iloc = df.iloc[:,o[0]:o[1]] #取指定列，下同
#             df_iloc.columns = head_col["原始词"] #替换标题头，下同
#             self.ori_vocab  = self.ori_vocab.append(df_iloc)
#             #is关系
#             df_iloc = df.iloc[:,o[0]:head_index["标准词"][0][1]]
#             df_iloc.columns = head_col["原始词"] +  head_col["标准词"]
#             self.is_rel = self.is_rel.append(df_iloc)
#         for i in range(len(head_index["标准词"])):
#             #标准词
#             df_iloc = df.iloc[:,head_index["标准词"][i][0]:head_index["标准词"][i][1]]
#             df_iloc.columns = head_col["标准词"]
#             self.std_vocab = self.std_vocab.append(df_iloc)
#             if i > 0:
#                 #belong_to关系
#                 df_iloc = df.iloc[:,head_index["标准词"][i - 1][0]:head_index["标准词"][i][1]]
#                 df_iloc.columns =  head_col["标准词"] + [(h + "_1") for h in head_col["标准词"]]
#                 self.belong_rel = self.belong_rel.append(df_iloc)
#
#     def head_index(self,df):
#         """
#         由标题获取原始词、标准词位置，输出以下格式
#         {
#             '原始词': [[0, 1]],
#             '标准词': [[1, 4]]
#         }
#         """
#         cols = df.columns.values.tolist()
#         col_dict = {}
#         ori_index = []
#         std_index = []
#         last_index = 0
#         for i in range(len(cols) + 1):
#             if i > 0:
#                 if i ==  len(cols) or "[name]" in cols[i]:
#                     if "原始词" in cols[i - 1]:
#                         ori_index.append([last_index,i])
#                     elif "标准词" in cols[i - 1]:
#                         std_index.append([last_index,i])
#                     last_index = i
#         col_dict["原始词"] = ori_index
#         col_dict["标准词"] = std_index
#         return col_dict
#
#
#     def head_col(self,df):
#         """
#          由标题获取原始词、标准词列名，输出以下格式
#         {
#             '原始词': ['原始词[name]'],
#             '标准词': ['标准词[name]', '标准词[class]', '标准词[code]', '标准词[code_add]']
#         }
#         """
#         cols = df.columns.values.tolist()
#         col_dict = {}
#         ori_col = []
#         std_col = []
#         for col in cols:
#             if "原始词" in col and col not in ori_col and len(re.findall(".\\d+",col)) == 0:
#                 ori_col.append(col)
#             elif "标准词" in col and col not in std_col and len(re.findall(".\\d+",col)) == 0:
#                 std_col.append(col)
#         col_dict["原始词"] = ori_col
#         col_dict["标准词"] = std_col
#         return  col_dict
#
#     def get_localtime(self):
#         return time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
#
# if __name__ == "__main__":
#     # try:
#         handler = CreateGraph()
#         path = 'D:\\资料\\数据采集\\临床诊断.xlsx'
#         print(handler.get_localtime() + "-----------开始任务------------")
#         handler.read_excel_save_csv(path)
#         handler.neo4j_load_csv('P10001')
#         print(handler.get_localtime() + "-----------结束任务------------")
#     # except Exception as e:
#     #     print(e)