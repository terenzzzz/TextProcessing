# Do we need to process the query
# Index mean in engine
# Query mean in engine
# The return in for_query
# Goal: Find The Best 10 Document  for each queries?
# What method to rank (queries has many words) term_weighting???

#index: {'santa': {3204: 1}, ..., 'monica': {3204: 1}}
# (1, ['articles', 'exist', 'deal', 'tss', 'time', 'sharing', 'system', 'operating', 'system', 'ibm', 'computers'])
import math
class Retrieve:
    
    # Create new Retrieve object storing index and term weighting
    # scheme. (You can extend this method, as required.)
    def __init__(self, index, term_weighting):
        self.index = index
        self.term_weighting = term_weighting
        self.num_docs = self.compute_number_of_documents()
        print('Running in ',self.term_weighting)
        print('Total docs: ',self.num_docs)

    def compute_number_of_documents(self):
        self.doc_ids = set() 
        for term in self.index:
            self.doc_ids.update(self.index[term])
        return len(self.doc_ids)
    

    # Method performing retrieval for a single query (which is 
    # represented as a list of preprocessed terms). Returns list 
    # of doc ids for relevant docs (in rank order).
    
    def for_query(self, query):
        result = {}
        # 调用processQuery处理query
        query = self.processQuery(query)
        
        # 构造向量
        docDict={}
        for docId in self.doc_ids:
            docDict[docId] = {}
        # Binary Mode
        if self.term_weighting == 'binary':
            # 判断query词是否出现在document中
            for docId in self.doc_ids:
                for k in query:
                    if k in self.index:
                        if docId in self.index[k]:
                            binaryNum = 1
                        else:
                            binaryNum = 0
                        docDict[docId][k] = binaryNum
            # 调用相似度计算返回结果
            result = self.simCalc_binary(docDict)
                    
        # TF(Term Frequency) Mode
        elif self.term_weighting == 'tf':
            # 计算关键词出现在每篇文章中的次数
            for docId in self.doc_ids:
               for k in query:
                  if k in self.index:
                      if docId in self.index[k]:
                          count = self.index[k][docId]
                      else:
                          count = 0
                      docDict[docId][k] = count
            
            # 调用相似度计算返回结果
            result = self.simCalc_tf(docDict, query)
    
        # TF.IDF
        else:
            # 计算关键词出现在每篇文章中的次数(tf)
            tfDict={}
            for docId in self.doc_ids:
                tfDict[docId] = {}
                for k in query:
                   if k in self.index:
                       if docId in self.index[k]:
                           count = self.index[k][docId]
                       else:
                           count = 0
                       tfDict[docId][k] = count
            
            # size od Collection(|D|)
            collectionSize = self.num_docs
            
            # number of documents containg w(df_w)
            # 多少个文件包含w
            numDocW = {}
            for k in query:
                numDocW[k] = {}
                if k in self.index:
                    numDoc = len(self.index[k])
                    numDocW[k] = numDoc

            # 计算document中的tfidf值
            tfIdfDict = {}
            for docId in self.doc_ids:
                tfIdfDict[docId] = {}
                for k in query:
                    if k in self.index:
                        tf = tfDict[docId][k]
                        idf = math.log(collectionSize/numDocW[k])
                        tfIdf = tf * idf
                        tfIdfDict[docId][k] = tfIdf
            
            # 计算query中的tfidf值
            queryTfIdf = {}
            for k in query:
                if k in self.index:
                    tf = query[k]
                    idf = math.log(collectionSize/numDocW[k])
                    tfIdf = tf * idf
                    queryTfIdf[k] = tfIdf
                    
            # 计算sim
            result = {}
            for docId in tfIdfDict:
                qdSum = 0
                pwdDSum = 0
                for k in tfIdfDict[docId]:
                    q = queryTfIdf[k]
                    d = tfIdfDict[docId][k]
                    qd = q * d
                    qdSum += qd
                    pwdDSum += d * d
                # 排除毫不相干的文件
                if pwdDSum == 0:
                    result[docId] = 0
                else:
                    cosVal = qdSum / math.sqrt(pwdDSum)
                    result[docId] = cosVal
                     
        # 调用排序返回相似度最大的十个
        return self.rankTop(result,10)

#==============================================================================
# Calculation
    # 相似度计算(Binary)
    def simCalc_binary(self,docDict):
        result = {}
        # 计算文件里有多少个Term
        docSize = {}
        for term in self.index:
            for docId in self.index[term]:
                if docId in docSize:
                    docSize[docId] += 1
                else:
                    docSize[docId] = 0
                    
        # 计算有多少词语又在文件中 又在query中
        for doc in docDict:
            valueList = list(docDict[doc].values())
            pwdDSum = docSize[doc]
            qdSum=0
            for val in valueList:
                if val == 1:
                    qdSum += 1
            # 通过计算cos获取sim值
            cosVal = qdSum / math.sqrt(pwdDSum)
            result[doc] = cosVal
        return result
    
    # 相似度计算(TF)
    def simCalc_tf(self,docDict,query):
        result = {}
        # 分母
        pwdDSum = {}
        for term in self.index:
            for docId in self.index[term]:
                if docId in pwdDSum:
                    pwdDSum[docId] += self.index[term][docId] * self.index[term][docId]
                else:
                    pwdDSum[docId] = self.index[term][docId] * self.index[term][docId]
               
        # 分子 qd
        for docId in docDict:
            qdSum = 0
            for term in docDict[docId]:
                d = docDict[docId][term]
                q = query[term]
                qdSum += d * q
            # 通过计算cos获取sim值
            cosVal = qdSum / math.sqrt(pwdDSum[docId])
            result[docId] = cosVal
        return result
    
    def simCalc_tfIdf(self,tfIdfDict,queryTfIdf):
        result = {}
        
        # 分子 qd
        for docId in tfIdfDict:
            qdSum = 0
            pwdDSum = 0
            for k in tfIdfDict[docId]:
                q = queryTfIdf[k]
                d = tfIdfDict[docId][k]
                qd = q * d
                qdSum += qd
                pwdDSum += tfIdfDict[docId][k] * tfIdfDict[docId][k]

            if pwdDSum == 0:
                result[docId] = 0
            else:
                cosVal = qdSum / math.sqrt(pwdDSum)
                result[docId] = cosVal
        return result

    
#==============================================================================
# Helper
    # 排序方法
    def rankTop(self,dict,size):
        top_10 = []
        sort = sorted(dict.items(),key=lambda x:-x[1])[:size]
        for docId,sim in sort:
            top_10.append(docId)
        return top_10
    
    # 处理queryList 返回set 排除重复词
    def processQuery(self,query):
        quertDict={}
        for q in query:
            if q in quertDict:
                quertDict[q] += 1
            else:
                quertDict[q] = 1
        return quertDict
