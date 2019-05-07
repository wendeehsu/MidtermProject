# Packages
 -  numpy
 -  pandas
 -  xlsxwriter
 -  jieba
 -  openpyxl
 -  sklearn

# Steps
1. put given csv and xlsx in the same folder
2. run the python file: `GenerateCompanynews.py`
> result: new file called: CompanyNews.xlsx
3. Run the python file: `SortStockData.py`
> result: new file called: SortedCompanyStocks.xlsx </br>
> this is the training set (2016-2017)
4. Run python file: `SortTestingStock.py`
> result: new file called: t_SortTestingStock.xlsx </br>
> this is the testing data (2018)
5. Run python file: `pipeline.py`
> result: in commandLine, it will print the keywords for 台積電 and the precision, recall
6. Run python file: `test.py`
> print the precision and recall for testing on 2018

# Result
> not good tbh...QQ
### Selected keywords to construct our vector space
['季線且',
 '類股僅',
 '大漲點',
 '金融股',
 '大立光',
 '表示法',
 '去年底',
 'iphone',
 '指數來',
 '億元以',
 '美國供',
 '股市',
 '三大類',
 '持續性',
 '分析法',
 '公司法',
 '美股續',
 '漲幅則',
 '今日',
 '營收估',
 '超億元',
 '經濟部',
 '國際上',
 '積電上',
 '台積法',
 '台幣元',
 '積電光',
 '成交量',
 '類股則',
 '反彈視',
 '今天',
 '股盤勢',
 '終場則',
 '法人',
 '台積電',
 '下跌股',
 '股盤面',
 '震盪盤',
 '帶動下',
 '第季季',
 '外資上',
 '台北市',
 '外資則',
 '台灣區',
 '超過點',
 '蘋果將',
 '市場則',
 '投信則',
 '市場並',
 '終場僅',
 '台股',
 '經濟學',
 '股價來',
 '台灣前',
 '影響力',
 '三大廠',
 '8500',
 '8700',
 '表現強',
 '反彈並',
 '行情表',
 '短線將',
 '整理表',
 '漲點作',
 '震盪下',
 '持續量',
 '預期將',
 '今年初',
 '超億元期',
 '股價以',
 '指數位',
 '大盤量',
 '投資人要',
 '電子期',
 '億元且',
 '電子個',
 '下跌',
 '指期則',
 '強勢類',
 '半導體',
 '美元',
 '營收創']
### Prediction accuracy on 2018
Error:85
Correct:37
Accuracy:0.303279
出手率: 0 (<-- our model predicts every artical as "Not obvious" > <)
  
