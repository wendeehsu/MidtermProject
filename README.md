# Packages
 -  numpy
 -  pandas
 -  xlsxwriter
 -  jieba
 -  openpyxl
 -  sklearn

# Steps
1. put given csv and xlsx in the same folder
2. run the python file: GenerateCompanynews.py
result: new file called: CompanyNews.xlsx
3. Run the python file: SortStockData.py
result: new file called: SortedCompanyStocks.xlsx
this the training set: 2016-2017
4. Run python file: SortTestingStock.py
result: new file called: t_SortTestingStock.xlsx
this is the testing data
5. Run python file: pipeline.py
result: in commandLine, it will print the keywords for 台積電 and the precision, recall
6. Run python file: test.py
print the precision and recall for testing on 2018
