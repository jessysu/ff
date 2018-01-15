
import re, datetime, time, secrets
from dateutil.relativedelta import relativedelta
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
    if not table_exist("ff_hindsight_request_log"):
        cur.execute("create table ff_hindsight_request_log ( \
                        request_dt datetime, \
                        request_path varchar(255), \
                        request_view varchar(45), \
                        rid_source varchar(45), \
                        rid_id varchar(255), \
                        ds datetime, \
                        de datetime, \
                        symbol varchar(10) \
                        )")
        cur.execute("create index ff_hindsight_request_log_i1 on ff_hindsight_request_log (request_dt)")
        cur.execute("create index ff_hindsight_request_log_i2 on ff_hindsight_request_log (symbol)")
        cur.execute("create index ff_hindsight_request_log_i3 on ff_hindsight_request_log (rid_source, rid_id)")
    return

def log_ff_hindsight_request(request, ld="", ds="", de="", ss=""):
    assure_log()
    cur = connection.cursor()
    cur.execute("insert into ff_hindsight_request_log ( \
                 request_dt, \
                 request_path, \
                 request_view, \
                 rid_source, \
                 rid_id, \
                 ds, \
                 de, \
                 symbol \
                 ) values (%s, %s, %s, %s, %s, %s, %s, %s)", 
                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 request.get_full_path()[:255],
                 ld,
                 'anonymous:ip', 
                 request.META.get('REMOTE_ADDR',''), 
                 ds, 
                 de, 
                 ss))
    return

SP500 = runsql("select symbol from ff_scan_symbols where datediff(now(),last_updated) < 60")
SP500 = [i['symbol'] for i in SP500]

def index(request):
    return hindsight_monthly(request)
    
def hindsight_monthly(request, ds="", de="", ss=""):
    if not ds:
        ds = request.GET.get('ds', '')
    if not de:
        de = request.GET.get('de', '')
    if not ss:
        ss = request.GET.get('ss', '').upper()
    maxD = datetime.datetime.now() - datetime.timedelta(hours=19)
    if maxD.weekday()>4:
        maxD -= datetime.timedelta(days=1)
        if maxD.weekday()>4:
            maxD -= datetime.timedelta(days=1)
    hard_min = datetime.datetime.now() - relativedelta(years=10)
    hard_max = datetime.datetime.now() - relativedelta(years=5)
    rs = {"SminD":hard_min.strftime("%m/%Y"), "EminD":hard_min.strftime("%m/%Y"), "SmaxD":maxD.strftime("%m/%Y"), "EmaxD":maxD.strftime("%m/%Y"), "SP500":SP500}

    r = re.compile('\d{2}/\d{4}')
    if not ds or not r.match(ds):
        random_years = secrets.choice(list(range(1,11)))
        ds = (datetime.datetime.now() - relativedelta(years=random_years)).strftime("%m/%Y")
    if not de or not r.match(de):
        de = (datetime.datetime.now() - datetime.timedelta(hours=19)).strftime("%m/%Y")
    if len(ss) > 5:
        ss = ""
#    if not ds or not de or not ss or len(ss)>5:
#        print("lacks info")
#        return render(request, 'hindsight_monthly.html', rs)
#    if not r.match(ds) or not r.match(de):
#        print("wrong month")
#        return render(request, 'hindsight_monthly.html', rs)
    if datetime.datetime.strptime(ds,"%m/%Y") < hard_min :
        ds = hard_min.strftime("%m/%Y")
    if datetime.datetime.strptime(de,"%m/%Y") < hard_max :
        de = hard_max.strftime("%m/%Y")
    while not runsql("select count(1) cnt from ff_stock_w2 where close_month='"+(datetime.datetime.strptime(de,"%m/%Y")).strftime("%Y%m")+"'")[0]['cnt']:
        de = (datetime.datetime.strptime(de,"%m/%Y") - relativedelta(months=1)).strftime("%m/%Y")
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
    
#    rawsql = "select count(1) cnt from ff_stock_w3 where start_month='"+_ds+"' and end_month='"+_de+"' and symbol='"+ss+"'"
#    s = runsql(rawsql)
#    if not s[0]['cnt']:
#        print("no symbol")
#        return render(request, 'hindsight_monthly.html', rs)
    
    log_ff_hindsight_request(request, ld="/hsm/", ds=es, de=ee, ss=ss)

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
    return render(request, 'hindsight_monthly.html', {**rs,**rs_,**rs__})
    



def hindsight_daily(request, ds="", de="", ss=""):
    if not ds:
        ds = request.GET.get('ds', '')
    if not de:
        de = request.GET.get('de', '')
    if not ss:
        ss = request.GET.get('ss', '').upper()
    maxD = datetime.datetime.now() - datetime.timedelta(hours=19)
    if maxD.weekday()>4:
        maxD -= datetime.timedelta(days=1)
        if maxD.weekday()>4:
            maxD -= datetime.timedelta(days=1)
    minD = datetime.datetime.now()-datetime.timedelta(days=180)
    if minD.weekday()>4:
        minD += datetime.timedelta(days=1)
        if minD.weekday()>4:
            minD += datetime.timedelta(days=1)
    hard_min = datetime.datetime.now() - relativedelta(months=7)
    hard_max = datetime.datetime.now() - relativedelta(months=6)
    rs = {"SminD":minD.strftime("%m/%d/%Y"), "EminD":minD.strftime("%m/%d/%Y"), "SmaxD":maxD.strftime("%m/%d/%Y"), "EmaxD":maxD.strftime("%m/%d/%Y"), "SP500":SP500}
    
    r = re.compile('\d{2}/\d{2}/\d{4}')
    if not de or not r.match(de):
        de = (datetime.datetime.now() - datetime.timedelta(hours=19)).strftime("%m/%d/%Y")
    if datetime.datetime.strptime(de,"%m/%d/%Y") < hard_max :
        de = hard_max.strftime("%m/%d/%Y")
    if not ds or not r.match(ds):
        daydiff = ((datetime.datetime.now()- datetime.timedelta(hours=19)) - datetime.datetime.strptime(de,"%m/%d/%Y")).days
        choices = [i for i in [7,14,21,30,60,90,120,180,210] if i>=daydiff]
        random_days = secrets.choice(choices)
        ds = (datetime.datetime.now() - relativedelta(days=random_days)).strftime("%m/%d/%Y")
    if datetime.datetime.strptime(ds,"%m/%d/%Y") < hard_min :
        ds = hard_min.strftime("%m/%d/%Y")
    if len(ss) > 5:
        ss = ""
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+(datetime.datetime.strptime(ds,"%m/%d/%Y")).strftime("%Y-%m-%d")+"'")[0]['cnt']:
        ds = (datetime.datetime.strptime(ds,"%m/%d/%Y") + relativedelta(days=1)).strftime("%m/%d/%Y")
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+(datetime.datetime.strptime(de,"%m/%d/%Y")).strftime("%Y-%m-%d")+"'")[0]['cnt']:
        de = (datetime.datetime.strptime(de,"%m/%d/%Y") - relativedelta(days=1)).strftime("%m/%d/%Y")
#    if not ds or not de or not ss or len(ss)>5:
#        print("lacks daily info")
#        return render(request, 'hindsight_daily.html', rs)
#    if not r.match(ds) or not r.match(de):
#        print("wrong date")
#        return render(request, 'hindsight_daily.html', rs)
    rs['EminD'] = ds
    rs['SmaxD'] = de
    _ds = ds.replace('/','-')
    _ds = _ds[6:] + "-" + _ds[:5]
    _de = de.replace('/','-')
    _de = _de[6:] + "-" + _de[:5]
#    rawsql = "select count(1) cnt from ff_stock_w5 where start_date='"+_ds+"' and end_date='"+_de+"' and symbol='"+ss+"'"
#    s = runsql(rawsql)
#    if not s[0]['cnt']:
#        print("no symbol")
#        return render(request, 'hindsight_daily.html', rs)
    
    log_ff_hindsight_request(request, ld="/hsd/", ds=datetime.datetime.strptime(ds,"%m/%d/%Y"), de=datetime.datetime.strptime(de,"%m/%d/%Y"), ss=ss)

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



def symbol_landing(request, ss="", d="180"):
    if len(ss)>5:
        print("symbol too long")
        return render(request, 'hindsight_daily.html', {})
    ss = ss.upper()
    
    if d.isdigit():
        d = int(d)
        if d > 1826:
            d = 1826
    else:
        d = 180
    ds = datetime.datetime.now() - datetime.timedelta(days=d)
    if ds.weekday()>4:
        ds += datetime.timedelta(days=1)
        if ds.weekday()>4:
            ds += datetime.timedelta(days=1)
    de = datetime.datetime.now() - datetime.timedelta(hours=19)
    if de.weekday()>4:
        de -= datetime.timedelta(days=1)
        if de.weekday()>4:
            de -= datetime.timedelta(days=1)
    rawsql = "select close_date, high, low, close, volume from ff_stock where symbol='"+ss+"' and close_date>'"+ds.strftime("%Y-%m-%d")+"'"
    symbol_line = runsql(rawsql)
    if len(symbol_line) == 0:
        print("no such symbol in system")
        return render(request, 'hindsight_daily.html', {})
    for s in symbol_line:
        s['close_date'] = 1000*time.mktime(s['close_date'].timetuple())

    if d < 210:
        rawsql = "select a.*, security, sector from ( \
                  select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w5 where start_date='"+ds.strftime("%Y-%m-%d")+"' and end_date='"+de.strftime("%Y-%m-%d")+"' and symbol='"+ss+"' \
                  ) a, ff_scan_symbols b where a.symbol=b.symbol order by rn"
    else:
        rawsql = "select a.*, security, sector from ( \
                  select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w3 where start_month='"+ds.strftime("%Y%m")+"' and end_month='"+de.strftime("%Y%m")+"' and symbol='"+ss+"' \
                  ) a, ff_scan_symbols b where a.symbol=b.symbol order by rn"
    symbol_desc = runsql(rawsql)
    symbol_desc = symbol_desc[0]
    symbol_desc['pr'] = get_rank(symbol_desc['rn'])
    symbol_best = runsql("select * from ff_stock_best where symbol='"+ss+"'")
    best_terms = []
    best_times = []
    for s in symbol_best:
        if s['rg'][:2] in [b['rg'][:2] for b in best_terms]:
            continue
        i = re.split('(\D+)',s['rg'])
        s['base_val'] = int(i[0])
        s['base_unit'] = i[1]
        s['best_val'] = int(i[2])
        s['best_unit'] = i[3]
        s['pr'] = get_rank(s['rn'])
        if s['start'].year == s['end'].year:
            s['same_year'] = True
        else:
            s['same_year'] = False
        s['c_diff'] = int(100*s['c_diff'])
        best_terms.append(s)
        if s['rg'][-2:] not in [b['rg'][-2:] for b in best_times]:
            best_times.append(s)
    rd = {'d': d, 'ss': ss, 'symbol_desc': symbol_desc, 'symbol_line':symbol_line, 'best_terms':best_terms, 'best_times':best_times}
    return render(request, 'symbol_landing.html', rd)