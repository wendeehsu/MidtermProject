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
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

xl = pd.ExcelFile("stock_data.xlsx")
sheets = ["上市2017", "上市2016", "上櫃2017", "上櫃2016"]
columnList = ['證券代碼', '年月日', '收盤價(元)']

# Create empty sheet for each stock data.
CompanyStock = {}
CompanyStockList = ['1301 台塑', '2330 台積電', '2317 鴻海', '1303 南亞', '2412 中華電', '1326 台化', '2454 聯發科', '2002 中鋼', '1216 統一', '2498 宏達電', '2308 台達電', '2882 國泰金'  ]
for i in CompanyStockList:
    CompanyStock[i] = pd.DataFrame(columns = columnList)

for sheet in sheets:
  df = xl.parse(sheet)
  data = df[columnList].copy() 
  del df

  for stock in CompanyStockList:
    CompanyStock[stock] = CompanyStock[stock].append(data.loc[data["證券代碼"] == stock], ignore_index = True)
  del data

# print output to excel
outputFile = "SortedCompanyStocks.xlsx"
with pd.ExcelWriter(outputFile, mode='a+') as writer:
  for stock in CompanyStockList:
    CompanyStock[stock] = CompanyStock[stock].sort_values('年月日', ascending=True)
    CompanyStock[stock].to_excel(writer, sheet_name = stock, index = False, engine = 'xlsxwriter')
