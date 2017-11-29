
import re, datetime, time
from django.db import connection
#from django.http import HttpResponse
from django.shortcuts import render

def runsql(s):
    cur = connection.cursor()
    cur.execute(s)
    columns = [col[0] for col in cur.description]
    return [
        dict(zip(columns, row))
        for row in cur.fetchall()
    ]

def table_exist(table):
    cur = connection.cursor()
    cur.execute("SHOW TABLES LIKE '"+table+"'")
    if cur.fetchone():
        return True
    else:
        return False

def index(request):
    
    ds = request.POST.get('ds', '')
    de = request.POST.get('de', '')
    ss = request.POST.get('ss', '')
    rs = {}
    
    r = re.compile('\d{2}/\d{4}')
    if not ds or not de or not ss or len(ss)>5:
        print("lacks info")
        return render(request, 'home.html', rs)
    if not r.match(ds) or not r.match(de):
        print("wrong month")
        return render(request, 'home.html', rs)
    _ds = ds.replace('/','')
    _ds = _ds[2:] + _ds[:2]
    _de = de.replace('/','')
    _de = _de[2:] + _de[:2]
    rawsql = "select count(1) cnt from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"'"
    s = runsql(rawsql)
    if not s[0]['cnt']:
        print("no symbol")
        return render(request, 'home.html', rs)
    
    cur = connection.cursor()
    if not table_exist("ff_hindsight_log"):
        cur.execute("create table ff_hindsight_log (request_dt datetime, requester_ip varchar(45), ds varchar(8), de varchar(8), symbol varchar(10))")
        cur.execute("create index ff_hindsight_log_i1 on ff_hindsight_log (request_dt)")
        cur.execute("create index ff_hindsight_log_i2 on ff_hindsight_log (symbol)")
        cur.execute("create index ff_hindsight_log_i3 on ff_hindsight_log (requester_ip)")
    cur.execute("insert into ff_hindsight_log (request_dt, requester_ip, ds, de, symbol) values (%s, %s, %s, %s, %s)", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.META.get('REMOTE_ADDR',''), _ds, _de, ss))

    rawsql = "select a.* from (select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' order by rn limit 10) a \
              union \
              select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"'"
    symbol_list = runsql(rawsql)
    rawsql = "select a.*, c_min, round((close-c_min)/c_min*100,2) gp, rn from ff_stock a, ff_stock_w2 c, \
              (select a.* from (select rn, symbol from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' order by rn limit 10) a union \
              select rn, symbol from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"' \
              ) b where a.symbol=b.symbol and DATE_FORMAT(a.close_date, '%Y%m') >= '"+_ds+"' and DATE_FORMAT(a.close_date, '%Y%m') <= '"+_de+"' \
              and b.symbol=c.symbol and c.close_month = '"+_ds+"'"
    symbol_line = runsql(rawsql)
    for s in symbol_line:
        s['close_date'] = 1000*time.mktime(s['close_date'].timetuple())
    rs = {"ds": ds, "de": de, "ss": ss, "symbol_list": symbol_list, "symbol_line": symbol_line}
    return render(request, 'home.html', rs)
    
