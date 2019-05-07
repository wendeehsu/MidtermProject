#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import xlsxwriter
import math
import re
import jieba
from datetime import datetime, timedelta
from openpyxl import load_workbook
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.feature_extraction.text import TfidfVectorizer
ffrom sklearn import svm
from sklearn.datasets import samples_generator
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_regression
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

def lcs(str_a, str_b):
  if len(str_a) == 0 or len(str_b) == 0:
    return 0
  
  lcs_str=""
  max_len = 0
  
  dp = [0 for _ in range(len(str_b) + 1)]
  for i in range(1, len(str_a) + 1):
    left_up = 0
    for j in range(1, len(str_b) + 1):
      up = dp[j]
      if str_a[i-1] == str_b[j-1]:
        dp[j] = left_up + 1
        max_len = max([max_len, dp[j]])
        if max_len == dp[j]:
          lcs_str = str_a[i-max_len:i]
      else:
        dp[j] = 0
      left_up = up
  return str(lcs_str)


def merge(str_a, str_b):   
#contain one another
  if(str_a in str_b):
    return str_b
  elif(str_b in str_a):
    return str_a

  result=""
  dup=lcs(str_a,str_b)

  s1=str_a.find(dup)
  s2=str_b.find(dup)
  e1=s1+len(dup)
  e2=s2+len(dup)
  
  if(s1 > s2 and (e1 == len(str_a))):
    result=str_a+str_b[s2+len(dup):len(str_b)]
  elif(s2 > s1 and (e2 == len(str_b))):
    result=str_b+str_a[s1+len(dup):len(str_a)]

  return result

# 決定兩個時間點價格漲或跌(σ的調整在這裡調)
def DetermineUpOrDown(p1, p2, q = 0.03):
    OverThreshhold = True
    UpDown = False
    if (abs(p1 - p2) / p1) >= q:
        OverThreshhold = True
        if ((p1 - p2) / p1) < 0:
            UpDown = True
        else:
            UpDown = False
    else:
        OverThreshhold = False  
    
    return OverThreshhold, UpDown

# 決定某間公司哪些日子是漲/跌/不明顯
def GetCompanyStockTrend(CompanyName, frequency = 5):
    '''
    決定某公司哪些時間是漲/跌/不明顯
    並存成3個List
    '''
    stock_data = xl.parse(CompanyName, header = 0)
    stock_time = stock_data["年月日"].tolist()
    stock_price = stock_data["收盤價(元)"].tolist()

    # 標記漲或跌的時間到對應清單裡
    List_Price_Up = []
    List_Price_Down = []
    List_Price_NoReaction = []
    for i in range(0, len(stock_price) - frequency):
        p1 = stock_price[i]
        p2 = stock_price[i + frequency]
        a, b = DetermineUpOrDown(p1, p2)
        if a == True and b == True:
            List_Price_Up.append(stock_time[i])
        elif a == True and b == False:
            List_Price_Down.append(stock_time[i])
        elif a == False:
            List_Price_NoReaction.append(stock_time[i])
    
    List_Price_Up = list(set(List_Price_Up))  
    List_Price_Down = list(set(List_Price_Down))  
    List_Price_NoReaction = list(set(List_Price_NoReaction))  
    #print(List_Price_Up)
    #print(List_Price_Down)
    #print(List_Price_NoReaction)
    
    return List_Price_Up, List_Price_Down, List_Price_NoReaction

# 決定某間公司哪些日子起漲/起跌/不明顯
def GetIntersection(companyName, threshhold = 0.02):
    '''
    找出週均線和月均線的交叉點
    並存成起漲/起跌/不明顯3個清單
    '''
    df = xl.parse(companyName)
    df["周均線"] = df["收盤價(元)"].rolling(window = 5).mean()
    df["月均線"] = df["收盤價(元)"].rolling(window = 20).mean()
    df["diff"] = df["周均線"] - df["月均線"]
    diffArray = df["diff"].to_numpy()
    PriceList = df["收盤價(元)"].tolist() # 多建立一個有所有收盤價的清單
    UpIndex = []
    DownIndex = []
    NotObviousIndex = [] # 多建立一個反應不明顯的清單
    for i in range(1, len(diffArray)):
        if diffArray[i - 1] * diffArray[i] < 0 and abs(diffArray[i]) > threshhold:
            if diffArray[i] > 0:
                UpIndex.append(i)
            else:
                DownIndex.append(i)
        elif abs(float(diffArray[i]))/PriceList[i-1] < 0.15:
            NotObviousIndex.append(i)

    UpIndex = list(set(UpIndex))
    DownIndex = list(set(DownIndex))
    NotObviousIndex = list(set(NotObviousIndex))

    return df.iloc[UpIndex]["年月日"].tolist(), df.iloc[DownIndex]["年月日"].tolist(), df.iloc[NotObviousIndex]["年月日"].tolist() # 多回傳一個清單

# 畫出單股的週均線和月均線變化
def DrawPlot(df):
    # gca stands for 'get current axis'
    ax = plt.gca()
    df.plot(kind='line',x='年月日',y='周均線',ax = ax)
    df.plot(kind='line',x='年月日',y='月均線', color = 'red', ax = ax)

# 將看漲(跌)時間清單處理成yyyy/mm/dd格式(要把01/01改成1/1形式以利後續比對)
def TimeFormate(time):
    t = str(time)
    return t[:4] + '/' + t[5:7].replace("0", "") + '/' + t[8:9].replace("0", "") + t[9:10]

# 把標題和內容黏起來，標題權重設為3倍
def EnhanceTitleWeight(news, w = 3):
    return news["content"] + news["title"] * w

# 拿出delta天前的日期
def GetTime(start, delta):
    t = datetime.strptime(start, "%Y/%m/%d")
    t -= timedelta(days = delta)
    return TimeFormate(t)

# 抓出看漲文章(List_Price_up_article),看跌文章(List_Price_Down_article)
def GetArticleFrom(dictionary, company, days = 1):
    '''
    input:
    dictionary 為 StockTrend (抓出看漲看跌文章) 或 Intersection (跌到漲或漲到跌文章)
    company 公司名
    days 時間區間長度
    return:
    若 dictionary 為 StockTrend:
        List_Price_up_article 看漲文章
        List_Price_Down_article 看跌文章
    若 dictionary 為 Intersection:
        List_Price_up_article 跌到漲文章
        List_Price_Down_article 漲到跌文章
    '''
    List_Price_Up_time = []
    List_Price_Down_time = []
    List_Price_NoReaction_time = []
    for i in dictionary[company]["up"]:
        List_Price_Up_time.append(TimeFormate(i))
    for i in dictionary[company]["down"]:
        List_Price_Down_time.append(TimeFormate(i))
    for i in dictionary[company]["NotObvious"]:
        List_Price_NoReaction_time.append(TimeFormate(i))

    List_Price_up_article = []
    List_Price_Down_article = []
    List_Price_NoReaction_article = []
    for i in List_Price_Up_time: # i = '2016-08-03'
        for j in range(days):
            chosenTime = GetTime(i,j)
            if chosenTime in time2content:
                List_Price_up_article.append(time2content[chosenTime])

    for i in List_Price_Down_time:
        for j in range(days):
            chosenTime = GetTime(i,j)
            if chosenTime in time2content:
                List_Price_Down_article.append(time2content[chosenTime])
    
    for i in List_Price_NoReaction_time:
        for j in range(days):
            chosenTime = GetTime(i,j)
            if chosenTime in time2content:
                List_Price_NoReaction_article.append(time2content[chosenTime])

    del List_Price_Up_time, List_Price_Down_time, List_Price_NoReaction_time

    return List_Price_up_article, List_Price_Down_article, List_Price_NoReaction_article

def get_tfidf_tool(corpus, top = 30):
    '''
    input: corpus 文章 List（ex. 所有台塑的看漲文章 CompanyArticles['台塑']["up"]）
    return: 前top個排序過的關鍵字
    '''
    vectorizer = TfidfVectorizer(tokenizer = jieba.cut, analyzer = 'word', min_df = 2, stop_words = stopwords)
    X = vectorizer.fit_transform(corpus)
    m = X.mean(axis=0).getA().reshape(-1)
    max_indexs = np.argsort(m)[::-1]
    tokens = np.array(vectorizer.get_feature_names())
    
    terms = vectorizer.get_feature_names()

    for i in range(len(terms)-16):
        for j in range(i+1, i+15):
            a = len(terms[i])
            b = len(terms[j])
            d = lcs(str(terms[i]), str(terms[j]))
            c = len(str(d))
            if(a+b-c!=0):
                if((c/(a+b-c)) >= 0.6):
                    terms[i]= (merge(str(terms[i]), str(terms[j])))

    sums = X.sum(axis=0)
    data = []
    for col, term in enumerate(terms):
        data.append((term, sums[0, col], sums[0, col]))
    ranking = pd.DataFrame(data, columns = ['term', 'tfidf', 'len_term'])
    for i in range(len(ranking["term"])):
        ranking.iat[i, 2] = len(ranking.iat[i, 0])*len(ranking.iat[i, 0])*ranking.iat[i, 1]
    ranking = ranking.sort_values('len_term', ascending=False)

    #return tokens[max_indexs]

    return ranking[:top]['term'].tolist()


# CompanyVector[""]

def TestOn(totalArticle, label, testData, company):

    token = CompanyVector[company]
    test_vector = np.array([token])
    X = np.zeros((len(totalArticle), len(token)))
    for i in range(len(totalArticle)):
        for j in range(len(token)):
            X[i, j] = totalArticle[i].count(token[j])
            test_vector[0, j] = testData.count(token[j])

    clf = SVC(gamma='auto')
    #clf = Pipeline([('vect', CountVectorizer()),
       #            ('tfidf', TfidfTransformer()),
        #           ('clf', MultinomialNB()),])
    clf.fit(X, label)
    test_vector = np.array(test_vector)
    
    return clf.predict(test_vector)[0]
  
def ConductKFold(company):
    print(company,": \n")
    up = list(set(CompanyArticles[company]["up2down"]))
    down = list(set(CompanyArticles[company]["down2up"]))

    sample = 50
    not_obvious = list(set(CompanyArticles[company]["down2up_up2down_not_obvious"]))
    print(len(up),len(down),len(not_obvious))
    not_obvious = not_obvious[:sample]
    X = np.array(up + down + not_obvious)
    # y = np.array(["up"] * len(up) + ["down"] * len(down)+['down2up_up2down_not_obvious']*len(not_obvious))
    y = np.array(["up2down"] * len(up) + ["down2up"] * len(down)+["down2up_up2down_not_obvious"]*sample)
    
    kf = KFold(n_splits=10, shuffle = True) # split to 10 parts with random index
    
    Correct = 0
    Error = 0
    TP = 0
    FP = 0
    FN = 0
    Action = 0

    for train_index, test_index in kf.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        for i in test_index:
            result = TestOn(X_train, y_train, X[i], company)
            print(i)
            if result == y[i]:
                Correct += 1
                if y[i] != "down2up_up2down_not_obvious":
                    TP += 1
            else:
                Error += 1
                if(y[i] == "down2up_up2down_not_obvious"):
                    FP += 1
                else:
                    FN += 1

            if result != "down2up_up2down_not_obvious":
                Action += 1
    
    print(Error, Correct, Action, TP, FP, FN)            
    return Error, Correct, Action, TP, FP, FN

Companies = ["台積電"]
company2Stock = {"台積電" : '2330 台積電'}

xl = pd.ExcelFile("SortedCompanyStocks.xlsx")
x2 = pd.ExcelFile("CompanyNews.xlsx")
stopwords = []
with open('stopword.txt', 'r', encoding = 'utf-8') as f1:
    for line in f1:
        stopwords.append(line.strip())
stopwords[-1] = ' '

StockTrend = {}
for company in Companies:
    stock = company2Stock[company]
    UpTime, DownTime, NoReaction = GetCompanyStockTrend(stock)
    UpTime, DownTime, NoReaction = list(set(UpTime)), list(set(DownTime)), list(set(NoReaction))
    StockTrend[company] = { "up" : UpTime, "down" : DownTime, "NotObvious" : NoReaction}

# 以後要拿看漲/跌/不明顯的時間資料的方式：
# StockTrend["台塑"]["up"] 上漲日期列
# StockTrend["台塑"]["down"] 下跌日期列
# StockTrend["台塑"]["NotObvious"] 沒有反映列

Intersection = {}
for company in Companies:
  stock = company2Stock[company]
  up, down, NotObvious = GetIntersection(stock)
  up, down, NotObvious = list(set(up)), list(set(down)), list(set(NotObvious))
  Intersection[company] = { "up": up, "down" : down, "NotObvious" : NotObvious}

# 以後要拿交叉點資料的方式：
# Intersection["台塑"]["up"] 跌往漲日期列
# Intersection["台塑"]["down"] 漲往跌日期列
# Intersection["台塑"]["NotObvious"] 不明顯列


CompanyArticles = {}
for company in Companies:
    # 製作出company (ex.台塑) 的time2content[time] = 文章
    raw_data = x2.parse(company).dropna()
    raw_company_content = EnhanceTitleWeight(raw_data).tolist() 
    raw_company_content_time = raw_data["post_time"].tolist()
    del raw_data
  
    company_content_time = []
    for i in raw_company_content_time:
        company_content_time.append(i[:9])
    time2content = dict()
    for i, time in enumerate(company_content_time):
        if time in time2content:
            time2content[time] += raw_company_content[i]
        else:
            time2content[time] = raw_company_content[i]
    del company_content_time

    # 把 看漲, 看跌, 漲到跌, 跌到漲 的文章都存進字典
    up, down, up_down_not_obvious = GetArticleFrom(StockTrend, company)
    down2up, up2down, down2up_up2down_not_obvious = GetArticleFrom(Intersection, company, 7)
    CompanyArticles[company] = {"up": up, "down" : down, "down2up" : down2up, "up2down" : up2down, "up_down_not_obvious" : up_down_not_obvious, "down2up_up2down_not_obvious" : down2up_up2down_not_obvious}

# 以後拿文章的方式：
# CompanyArticles['台塑']["up"]                            看漲文章
# CompanyArticles['台塑']["down"]                          看跌文章
# CompanyArticles['台塑']["up_down_not_obvious"]           看跌看漲不明顯文章
# CompanyArticles['台塑']["down2up"]                       漲到跌文章
# CompanyArticles['台塑']["up2down"]                       跌到漲文章
# CompanyArticles['台塑']["down2up_up2down_not_obvious"]   跌到漲+漲到跌不明顯文章
CompanyVector = {}
for company in Companies:
    print(company,"keywords:")
    a = get_tfidf_tool(CompanyArticles[company]["up"], top = 50)
    b = get_tfidf_tool(CompanyArticles[company]["down"], top = 50)
    CompanyVector[company] = list(set(a+b))

for company in Companies:
    print(company,"看漲文章:",len(CompanyArticles[company]["up"]))    
    print(company,"看跌文章:",len(CompanyArticles[company]["down"]))
    print(company,"看跌看漲不明顯文章:",len(CompanyArticles[company]["up_down_not_obvious"]))    
    print(company,"漲到跌文章:",len(CompanyArticles[company]["down2up"]))    
    print(company,"跌到漲文章:",len(CompanyArticles[company]["up2down"]))    
    print(company,"跌到漲+漲到跌不明顯文章:",len(CompanyArticles[company]["down2up_up2down_not_obvious"]))    

Errors = []
Corrects = []
Ratio = []
Actions = []


for company in Companies:
    print(company,"看漲文章:",len(set(CompanyArticles[company]["up"])))    
    print(company,"看跌文章:",len(set(CompanyArticles[company]["down"])))
    print(company,"看跌看漲不明顯文章:",len(set(CompanyArticles[company]["up_down_not_obvious"])))    
    print(company,"漲到跌文章:",len(set(CompanyArticles[company]["down2up"])))    
    print(company,"跌到漲文章:",len(set(CompanyArticles[company]["up2down"])))    
    print(company,"跌到漲+漲到跌不明顯文章:",len(set(CompanyArticles[company]["down2up_up2down_not_obvious"])))    

for company in Companies:
    Error, Correct, Action, TP, FP, FN = ConductKFold(company)
    Errors.append(Error)
    Corrects.append(Correct)

    Ratio.append(float(Correct)/(Error+Correct))
    Actions.append(float(Action)/(Error+Correct))
    print(Error, Correct, Action)

    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    #positive: 有反轉點
    #false positive: 沒有反轉點 認為有
    #fales negative: 有反轉點 覺得沒有
print(pd.DataFrame({"company":Companies, "Error": Errors, "Correct": Corrects, "Rate": Ratio, "Action":Actions}))
print("Precision", precision, "Recall", recall)
