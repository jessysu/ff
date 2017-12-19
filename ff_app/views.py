
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

def get_rank(r):
    R = list("ABCDE")
    S = ['+','','-']
    q = r // 20
    if q > 14:
        o = "F"
    else:
        o = R[int(q // 3)] + S[int(q % 3)]
    return o

def assure_log():
    cur = connection.cursor()
    if not table_exist("ff_hindsight_log"):
        cur.execute("create table ff_hindsight_log (request_dt datetime, requester_ip varchar(45), ds varchar(8), de varchar(8), symbol varchar(10))")
        cur.execute("create index ff_hindsight_log_i1 on ff_hindsight_log (request_dt)")
        cur.execute("create index ff_hindsight_log_i2 on ff_hindsight_log (symbol)")
        cur.execute("create index ff_hindsight_log_i3 on ff_hindsight_log (requester_ip)")
    if not table_exist("ff_hindsight_dlog"):
        cur.execute("create table ff_hindsight_dlog (request_dt datetime, requester_ip varchar(45), ds date, de date, symbol varchar(10))")
        cur.execute("create index ff_hindsight_dlog_i1 on ff_hindsight_dlog (request_dt)")
        cur.execute("create index ff_hindsight_dlog_i2 on ff_hindsight_dlog (symbol)")
        cur.execute("create index ff_hindsight_dlog_i3 on ff_hindsight_dlog (requester_ip)")
    return



SP500 = runsql("select symbol from ff_scan_symbols where datediff(now(),last_updated) < 60")
SP500 = [i['symbol'] for i in SP500]

def index(request):
    
    ds = request.POST.get('ds', '')
    de = request.POST.get('de', '')
    ss = request.POST.get('ss', '').upper()
    maxD = datetime.datetime.now() - datetime.timedelta(hours=19)
    if maxD.weekday()>4:
        maxD -= datetime.timedelta(days=1)
        if maxD.weekday()>4:
            maxD -= datetime.timedelta(days=1)
    rs = {"SminD":"11/2002", "EminD":"11/2002", "SmaxD":maxD.strftime("%m/%Y"), "EmaxD":maxD.strftime("%m/%Y"), "SP500":SP500}

    r = re.compile('\d{2}/\d{4}')
    if not ds or not de or not ss or len(ss)>5:
        print("lacks info")
        return render(request, 'home.html', rs)
    if not r.match(ds) or not r.match(de):
        print("wrong month")
        return render(request, 'home.html', rs)
    rs['EminD'] = ds
    rs['SmaxD'] = de
    _ds = ds.replace('/','')
    _ds = _ds[2:] + _ds[:2]
    _de = de.replace('/','')
    _de = _de[2:] + _de[:2]
    es = datetime.datetime.strptime(ds,"%m/%Y")
    ee = datetime.datetime.strptime(de,"%m/%Y")
    sy = es.year == ee.year
    rs__ = {"es":es, "ee":ee, "sy": sy}
    
    rawsql = "select count(1) cnt from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"'"
    s = runsql(rawsql)
    if not s[0]['cnt']:
        print("no symbol")
        return render(request, 'home.html', rs)
    
    assure_log()
    cur = connection.cursor()
    cur.execute("insert into ff_hindsight_log (request_dt, requester_ip, ds, de, symbol) values (%s, %s, %s, %s, %s)", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.META.get('REMOTE_ADDR',''), _ds, _de, ss))

    rawsql = "select a.*, security, sector from ( \
              select a.* from (select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' order by rn limit 10) a \
              union \
              select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"' \
              ) a, ff_scan_symbols b where a.symbol=b.symbol order by rn"
    symbol_list = runsql(rawsql)
    pr = ""
    for i in symbol_list:
        if i['symbol'] == ss:
            pr = get_rank(i['rn'])
    rawsql = "select a.*, c_min, round((close-c_min)/c_min*100,2) gp, rn from ff_stock a, ff_stock_w2 c, \
              (select a.* from (select rn, symbol from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' order by rn limit 10) a union \
              select rn, symbol from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"' \
              ) b where a.symbol=b.symbol and DATE_FORMAT(a.close_date, '%Y%m') >= '"+_ds+"' and DATE_FORMAT(a.close_date, '%Y%m') <= '"+_de+"' \
              and b.symbol=c.symbol and c.close_month = '"+_ds+"'"
    symbol_line = runsql(rawsql)
    for s in symbol_line:
        s['close_date'] = 1000*time.mktime(s['close_date'].timetuple())
    rs_ = {"ds": ds, "de": de, "ss": ss, "symbol_list": symbol_list, "symbol_line": symbol_line, "pr":pr}
    return render(request, 'home.html', {**rs,**rs_,**rs__})
    



def hindsight_daily(request):
    
    ds = request.POST.get('ds', '')
    de = request.POST.get('de', '')
    ss = request.POST.get('ss', '').upper()
    maxD = datetime.datetime.now() - datetime.timedelta(hours=19)
    if maxD.weekday()>4:
        maxD -= datetime.timedelta(days=1)
        if maxD.weekday()>4:
            maxD -= datetime.timedelta(days=1)
    minD = datetime.datetime.now()-datetime.timedelta(days=90)
    rs = {"SminD":minD.strftime("%m/%d/%Y"), "EminD":minD.strftime("%m/%d/%Y"), "SmaxD":maxD.strftime("%m/%d/%Y"), "EmaxD":maxD.strftime("%m/%d/%Y"), "SP500":SP500}
    
    r = re.compile('\d{2}/\d{2}/\d{4}')
    if not ds or not de or not ss or len(ss)>5:
        print("lacks daily info")
        return render(request, 'hindsight_daily.html', rs)
    if not r.match(ds) or not r.match(de):
        print("wrong date")
        return render(request, 'hindsight_daily.html', rs)
    rs['EminD'] = ds
    rs['SmaxD'] = de
    _ds = ds.replace('/','-')
    _ds = _ds[6:] + "-" + _ds[:5]
    _de = de.replace('/','-')
    _de = _de[6:] + "-" + _de[:5]
    rawsql = "select count(1) cnt from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' and symbol='"+ss+"'"
    s = runsql(rawsql)
    if not s[0]['cnt']:
        print("no symbol")
        return render(request, 'hindsight_daily.html', rs)
    
    assure_log()
    cur = connection.cursor()
    cur.execute("insert into ff_hindsight_dlog (request_dt, requester_ip, ds, de, symbol) values (%s, %s, %s, %s, %s)", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request.META.get('REMOTE_ADDR',''), _ds, _de, ss))

    rawsql = "select a.*, security, sector from ( \
              select a.* from (select rn+1 rn, symbol, round(c_diff*100,2) c_diff from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' order by rn limit 10) a \
              union \
              select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' and symbol='"+ss+"' \
              ) a, ff_scan_symbols b where a.symbol=b.symbol order by rn"
    symbol_list = runsql(rawsql)
    pr = ""
    for i in symbol_list:
        if i['symbol'] == ss:
            pr = get_rank(i['rn'])
    rawsql = "select a.*, round((a.close-c.low)/c.low*100,2) gp, rn from ff_stock a, ff_stock_w4 c, \
              (select a.* from (select rn, symbol from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' order by rn limit 10) a union \
              select rn, symbol from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' and symbol='"+ss+"' \
              ) b where a.symbol=b.symbol and a.close_date >= '"+_ds+"' and a.close_date <= '"+_de+"' \
              and b.symbol=c.symbol and c.close_date = '"+_ds+"'"
    symbol_line = runsql(rawsql)
    for s in symbol_line:
        s['close_date'] = 1000*time.mktime(s['close_date'].timetuple())
    rs_ = {"ds": ds, "de": de, "ss": ss, "symbol_list": symbol_list, "symbol_line": symbol_line, "pr":pr}
    return render(request, 'hindsight_daily.html', {**rs,**rs_})
