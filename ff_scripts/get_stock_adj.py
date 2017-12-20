# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 21:19:08 2017

@author: jsu
"""

#pip install pandas-datareader
from pandas_datareader import data
from pandas_datareader.google.daily import GoogleDailyReader
import datetime, time

from util_mysql import table_exist, runsql, runsqlmany, fetch_rawsql, dbcommit
from get_sp500 import refresh_sp500

### fix google url issue ##
@property
def url(self):
    return 'http://finance.google.com/finance/historical'
GoogleDailyReader.url = url
############################

FF_STOCK_ADJ_DDL = """create table ff_stock_adj (
symbol varchar(10),
close_date date, 
close float
)
""".replace('\n', ' ').replace('\r', '')

def assure_required_tables():
    if not table_exist("ff_stock_adj"):
        runsql(FF_STOCK_ADJ_DDL)
    if not table_exist("ff_scan_symbols"):
        refresh_sp500()



assure_required_tables()

symbols = fetch_rawsql("select symbol from ff_scan_symbols")
symbols = [i['symbol'] for i in symbols]


#ibm = pdr.get_data_yahoo(symbols='IBM', start=datetime(2000, 1, 1), end=datetime(2012, 1, 1))
#print(ibm['Adj Close'])

#symbols = [symbols[0]]
for s in symbols:
    try:
        d = data.DataReader(s, 'google', datetime.datetime(2000, 1, 1), datetime.datetime.now())
        t1 = d['Close'].values.tolist()
        t2 = d.index.tolist()
        T = [(s,)+(b.to_pydatetime().strftime('%Y-%m-%d'),)+(a,) for a,b in zip(t1,t2)]
        runsqlmany("insert into ff_stock_adj (symbol, close_date, close) values (%s, %s, %s)", T)
        dbcommit()
        print("Done ..."+s+" ... "+time.strftime('%Y-%m-%d %H:%M:%S'))
    except:
        print("Error and skipped ..."+s+" ... "+time.strftime('%Y-%m-%d %H:%M:%S'))
    time.sleep(5)

if table_exist('ff_stock'):
    c1 = fetch_rawsql("select count(1) cnt from ff_stock_adj")[0]['cnt']
    c2 = fetch_rawsql("select count(1) cnt from ff_stock")[0]['cnt']
    if c1 > c2:
        runsql("drop table ff_stock")
        runsql("alter table ff_stock_adj rename to ff_stock")
    else:
        if table_exist('ff_stock_fail'):
            runsql("drop table ff_stock_fail")
        runsql("alter table ff_stock_adj rename to ff_stock_fail")
    dbcommit()
else:
    runsql("alter table ff_stock_adj rename to ff_stock")
    dbcommit()
runsql("create index ff_stock_i1 on ff_stock (symbol, close_date)")
dbcommit()

