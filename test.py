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

Companies = ["台積電"]

company2Stock = {
    "台積電" : '2330 台積電',
    "鴻海" : '2317 鴻海',
    "台塑" : '1301 台塑',
    "南亞" : '1303 南亞',
    "中華電" : '2412 中華電',
    "台化" : '1326 台化',
    "聯發科" : '2454 聯發科',
    "中鋼" : '2002 中鋼',
    "統一" : '1216 統一',
    "宏達電" : '2498 宏達電',
    "台達電" : '2308 台達電',
    "國泰金" : '2882 國泰金'
}

xl = pd.ExcelFile("SortedCompanyStocks.xlsx")
x2 = pd.ExcelFile("CompanyNews.xlsx")
test_xl = pd.ExcelFile("t_SortedCompanyStocks.xlsx")

# 決定兩個時間點價格漲或跌(σ的調整在這裡調)
def DetermineUpOrDown(p1, p2, q = 0.04):
  '''
  決定兩時間點p1和p2收盤價變化
  是否高於門檻q(OverThreshhold = True)
  是否為漲(UpDown = True)
  '''
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
def t_GetCompanyStockTrend(CompanyName, frequency = 10):
  '''
  決定某公司哪些時間是漲/跌/不明顯
  並存成3個List
  '''
  stock_data = test_xl.parse(CompanyName, header = 0)
  stock_time = stock_data["年月日"].tolist()
  stock_price = stock_data["收盤價(元)"].tolist()
  print(stock_data.head())
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
      
  #print(List_Price_Up)
  #print(List_Price_Down)
  #print(List_Price_NoReaction)
  
  return List_Price_Up, List_Price_Down, List_Price_NoReaction

# 決定某間公司 in 2018 哪些日子起漲/起跌/不明顯
def t_GetIntersection(companyName):
  '''
  找出週均線和月均線的交叉點
  並存成起漲/起跌/不明顯3個清單
  '''
  df = test_xl.parse(companyName)
  df["周均線"] = df["收盤價(元)"].rolling(window = 5).mean()
  df["月均線"] = df["收盤價(元)"].rolling(window = 20).mean()
  df["diff"] = df["周均線"] - df["月均線"]
  week_mean = df["周均線"].to_numpy()
  month_mean = df["月均線"].to_numpy()
  diffArray = df["diff"].to_numpy()
  PriceList = df["收盤價(元)"].tolist() # 多建立一個有所有收盤價的清單
  UpIndex = []
  DownIndex = []
  NotObviousIndex = [] # 多建立一個反應不明顯的清單
  for i in range(1, len(diffArray)-20):
    if diffArray[i + 1] * diffArray[i] < 0:
      if DetermineUpOrDown(PriceList[i + 1], PriceList[i + 5]) == (True, True):
        UpIndex.append(i)
      elif DetermineUpOrDown(PriceList[i + 1], PriceList[i + 5]) == (True, False):
        DownIndex.append(i)
      else:
        NotObviousIndex.append(i)
  return df.iloc[UpIndex]["年月日"].tolist(), df.iloc[DownIndex]["年月日"].tolist(), df.iloc[NotObviousIndex]["年月日"].tolist() # 多回傳一個清單

# 決定某間公司哪些日子是漲/跌/不明顯
def GetCompanyStockTrend(CompanyName, frequency = 10):
  '''
  決定某公司哪些時間是漲/跌/不明顯
  並存成3個List
  '''
  stock_data = xl.parse(CompanyName, header = 0)
  stock_time = stock_data["年月日"].tolist()
  stock_price = stock_data["收盤價(元)"].tolist()
  print(stock_data.head())
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
      
  #print(List_Price_Up)
  #print(List_Price_Down)
  #print(List_Price_NoReaction)
  
  return List_Price_Up, List_Price_Down, List_Price_NoReaction

# 決定某間公司哪些日子起漲/起跌/不明顯
def GetIntersection(companyName):
  '''
  找出週均線和月均線的交叉點
  並存成起漲/起跌/不明顯3個清單
  '''
  df = xl.parse(companyName)
  df["周均線"] = df["收盤價(元)"].rolling(window = 5).mean()
  df["月均線"] = df["收盤價(元)"].rolling(window = 20).mean()
  df["diff"] = df["周均線"] - df["月均線"]
  week_mean = df["周均線"].to_numpy()
  month_mean = df["月均線"].to_numpy()
  diffArray = df["diff"].to_numpy()
  PriceList = df["收盤價(元)"].tolist() # 多建立一個有所有收盤價的清單
  UpIndex = []
  DownIndex = []
  NotObviousIndex = [] # 多建立一個反應不明顯的清單
  for i in range(1, len(diffArray)-20):
    if diffArray[i + 1] * diffArray[i] < 0:
      if DetermineUpOrDown(PriceList[i + 1], PriceList[i + 5]) == (True, True):
        UpIndex.append(i)
      elif DetermineUpOrDown(PriceList[i + 1], PriceList[i + 5]) == (True, False):
        DownIndex.append(i)
      else:
        NotObviousIndex.append(i)
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
  
  del List_Price_Up_time, List_Price_Down_time
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
  sums = X.sum(axis=0)
  data = []
  for col, term in enumerate(terms):
    data.append((term, sums[0, col], sums[0, col]))
  ranking = pd.DataFrame(data, columns = ['term', 'tfidf', 'len_term'])
  for i in range(len(ranking["term"])):
    ranking.iat[i, 2] = len(ranking.iat[i, 0])*len(ranking.iat[i, 0])*ranking.iat[i, 1]
  ranking = ranking.sort_values('len_term', ascending=False)

  count = 0
  pos = 0
  while(count <= 30):
    if(len(ranking.iat[pos,0]) >= 2):
      print(ranking.iat[pos, 0])
      count +=1
    pos +=1

  return ranking[:top]['term'].tolist()

stopwords = []
with open('stopword.txt', 'r', encoding = 'utf-8') as f1:
  for line in f1:
    stopwords.append(line.strip())
stopwords[-1] = ' '


StockTrend = {}
t_StockTrend = {}
for company in Companies:
  stock = company2Stock[company]
#   UpTime, DownTime = GetCompanyStockTrend(stock)
  UpTime, DownTime, NoReaction = GetCompanyStockTrend(stock)
  t_UpTime, t_DownTime, t_NoReaction = t_GetCompanyStockTrend(stock)
  StockTrend[company] = { "up" : UpTime, "down" : DownTime, "NotObvious" : NoReaction}
  t_StockTrend[company] = { "up" : t_UpTime, "down" : t_DownTime, "NotObvious" : t_NoReaction}
  up, down, up_down_not_obvious = GetArticleFrom(StockTrend, company)
  t_up, t_down, t_up_down_not_obvious = GetArticleFrom(RealAnswer, company)
  CompanyArticles[company] = {"up": up, "down" : down, "up_down_not_obvious" : up_down_not_obvious}
