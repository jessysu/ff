
import re, datetime, time, secrets
from dateutil.relativedelta import relativedelta
from django.db import connection
#from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages

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


def generate_ranged_query():
    cdt = datetime.datetime.now() - datetime.timedelta(hours=19)
    rq = []
    rq.append({"term": "5 years", "link":"/hsm/?ds="+(cdt-relativedelta(years=5)).strftime("%m/%Y&de=")+cdt.strftime("%m/%Y&ss=")})
    rq.append({"term": "3 years", "link":"/hsm/?ds="+(cdt-relativedelta(years=3)).strftime("%m/%Y&de=")+cdt.strftime("%m/%Y&ss=")})
    rq.append({"term": "1 year", "link":"/hsm/?ds="+(cdt-relativedelta(years=1)).strftime("%m/%Y&de=")+cdt.strftime("%m/%Y&ss=")})
    rq.append({"term": "6 months", "link":"/hsd/?ds="+(cdt-relativedelta(months=6)).strftime("%m/%d/%Y&de=")+cdt.strftime("%m/%d/%Y&ss=")})
    rq.append({"term": "3 months", "link":"/hsd/?ds="+(cdt-relativedelta(months=3)).strftime("%m/%d/%Y&de=")+cdt.strftime("%m/%d/%Y&ss=")})
    rq.append({"term": "1 month", "link":"/hsd/?ds="+(cdt-relativedelta(months=1)).strftime("%m/%d/%Y&de=")+cdt.strftime("%m/%d/%Y&ss=")})
    rq.append({"term": "2 weeks", "link":"/hsd/?ds="+(cdt-relativedelta(days=14)).strftime("%m/%d/%Y&de=")+cdt.strftime("%m/%d/%Y&ss=")})
    rq.append({"term": "1 week", "link":"/hsd/?ds="+(cdt-relativedelta(days=7)).strftime("%m/%d/%Y&de=")+cdt.strftime("%m/%d/%Y&ss=")})
    return rq

SP500 = runsql("select symbol from ff_scan_symbols where datediff(now(),last_updated) < 60")
SP500 = [i['symbol'] for i in SP500]

def index(request):
    return redirect("/hsd/")

def about(request):
    return render(request, 'about.html', {})


    
def hindsight_monthly(request, ds="", de="", ss=""):
    to_be_redir = False
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
    SminD = hard_min.strftime("%m/%Y")
    EminD = hard_min.strftime("%m/%Y") 
    SmaxD = maxD.strftime("%m/%Y")
    EmaxD = maxD.strftime("%m/%Y")

    r = re.compile('\d{2}/\d{4}')
    if not ds or not r.match(ds):
        to_be_redir = True
        random_years = secrets.choice(list(range(1,6)))
        ds = (datetime.datetime.now() - relativedelta(years=random_years)).strftime("%m/%Y")
        messages.warning(request, 'Showing the top stock symbols during the last <strong>'+str(random_years)+'</strong> years.')
    if not de or not r.match(de):
        to_be_redir = True
        de = (datetime.datetime.now() - datetime.timedelta(hours=19)).strftime("%m/%Y")
    if len(ss) > 5:
        to_be_redir = True
        ss = ""
    if datetime.datetime.strptime(de,"%m/%Y") > maxD :
        to_be_redir = True
        de = maxD.strftime("%m/%Y")
        messages.warning(request, 'Showing the top stocks up to current time only.')
    if datetime.datetime.strptime(ds,"%m/%Y") < datetime.datetime.strptime(hard_min.strftime("%m/%Y"),"%m/%Y") :
        to_be_redir = True
        ds = hard_min.strftime("%m/%Y")
        messages.warning(request, 'Showing the top stock symbols during the last <strong>10</strong> years only.')
    if datetime.datetime.strptime(de,"%m/%Y") < hard_max :
        to_be_redir = True
        de = hard_max.strftime("%m/%Y")
        messages.warning(request, 'The end date needs to be within the last <strong>5</strong> years. Fixed.')
    while not runsql("select count(1) cnt from ff_stock_w2 where close_month='"+(datetime.datetime.strptime(de,"%m/%Y")).strftime("%Y%m")+"'")[0]['cnt']:
        to_be_redir = True
        de = (datetime.datetime.strptime(de,"%m/%Y") - relativedelta(months=1)).strftime("%m/%Y")
    if to_be_redir:
        return redirect("/hsm/?ds="+ds.replace("/","%2F")+"&de="+de.replace("/","%2F")+"&ss="+ss)
    EminD = ds
    SmaxD = de
    _ds = ds.replace('/','')
    _ds = _ds[2:] + _ds[:2]
    _de = de.replace('/','')
    _de = _de[2:] + _de[:2]
    es = datetime.datetime.strptime(ds,"%m/%Y")
    ee = datetime.datetime.strptime(de,"%m/%Y")
    sy = es.year == ee.year
    
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
    rs = {"SminD": SminD, "EminD": EminD, "SmaxD": SmaxD, "EmaxD": EmaxD,
          "es": es, "ee": ee, "sy": sy,
          "ds": ds, "de": de, "ss": ss, 
          "symbol_list": symbol_list, "symbol_line": symbol_line, 
          "pr": pr, "SP500": SP500, "rq": generate_ranged_query()
          }
    return render(request, 'hindsight_monthly.html', rs)
    



def hindsight_daily(request, ds="", de="", ss=""):
    to_be_redir = False
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
    SminD = minD.strftime("%m/%d/%Y")
    EminD = minD.strftime("%m/%d/%Y")
    SmaxD = maxD.strftime("%m/%d/%Y")
    EmaxD = maxD.strftime("%m/%d/%Y")
    
    r = re.compile('\d{2}/\d{2}/\d{4}')
    if not de or not r.match(de):
        to_be_redir = True
        de = (datetime.datetime.now() - datetime.timedelta(hours=19)).strftime("%m/%d/%Y")
    if datetime.datetime.strptime(de,"%m/%d/%Y") < hard_max :
        to_be_redir = True
        de = hard_max.strftime("%m/%d/%Y")
        messages.warning(request, 'The end date needs to be within the last <strong>6</strong> months. Fixed.')
    if datetime.datetime.strptime(de,"%m/%d/%Y") > maxD :
        to_be_redir = True
        de = maxD.strftime("%m/%d/%Y")
        messages.warning(request, 'Showing the top stocks up to current time only.')
    if not ds or not r.match(ds):
        to_be_redir = True
        daydiff = ((datetime.datetime.now()- datetime.timedelta(hours=19)) - datetime.datetime.strptime(de,"%m/%d/%Y")).days
        choices = [i for i in [7,14,21,30,60,90,120,180,210] if i>=daydiff]
        random_days = secrets.choice(choices)
        ds = (datetime.datetime.now() - relativedelta(days=random_days)).strftime("%m/%d/%Y")
    if datetime.datetime.strptime(ds,"%m/%d/%Y") < hard_min :
        ds = (datetime.datetime.strptime(ds,"%m/%d/%Y")).strftime("%m/%Y")
        de = (datetime.datetime.strptime(de,"%m/%d/%Y")).strftime("%m/%Y")
        messages.warning(request, 'Changed to monthly resolution for period longer than 6 months.')
        return redirect("/hsm/?ds="+ds.replace("/","%2F")+"&de="+de.replace("/","%2F")+"&ss="+ss)
    if len(ss) > 5:
        to_be_redir = True
        ss = ""
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+(datetime.datetime.strptime(ds,"%m/%d/%Y")).strftime("%Y-%m-%d")+"'")[0]['cnt']:
        to_be_redir = True
        ds = (datetime.datetime.strptime(ds,"%m/%d/%Y") + relativedelta(days=1)).strftime("%m/%d/%Y")
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+(datetime.datetime.strptime(de,"%m/%d/%Y")).strftime("%Y-%m-%d")+"'")[0]['cnt']:
        to_be_redir = True
        de = (datetime.datetime.strptime(de,"%m/%d/%Y") - relativedelta(days=1)).strftime("%m/%d/%Y")
    if to_be_redir:
        return redirect("/hsd/?ds="+ds.replace("/","%2F")+"&de="+de.replace("/","%2F")+"&ss="+ss)
    EminD = ds
    SmaxD = de
    _ds = ds.replace('/','-')
    _ds = _ds[6:] + "-" + _ds[:5]
    _de = de.replace('/','-')
    _de = _de[6:] + "-" + _de[:5]
    
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
    rs = {"SminD":SminD, "EminD":EminD, "SmaxD":SmaxD, "EmaxD":EmaxD,
          "ds": ds, "de": de, "ss": ss, 
          "symbol_list": symbol_list, "symbol_line": symbol_line, 
          "pr":pr, "SP500":SP500, "rq": generate_ranged_query()
          }
    return render(request, 'hindsight_daily.html', rs)



def symbol_landing(request, ss="", d="180"):
    if not ss or len(ss)>5:
        messages.warning(request, 'Invalid stock symbol.')
        return redirect("/hsd/")
    ss = ss.upper()
    
    if d.isdigit():
        d = int(d)
        if d > 365:
            messages.warning(request, 'Only showing quotes for up to the past 365 days.')
            return redirect("/sym/"+ss+"/365/")
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
        messages.warning(request, 'No data for the stock symbol <b>'+ss+'</b>')
        return redirect("/hsd/")
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+ds.strftime("%Y-%m-%d")+"'")[0]['cnt']:
        ds += relativedelta(days=1)
    while not runsql("select count(1) cnt from ff_stock_w4 where close_date='"+de.strftime("%Y-%m-%d")+"'")[0]['cnt']:
        de -= relativedelta(days=1)
    for s in symbol_line:
        s['close_date'] = 1000*time.mktime(s['close_date'].timetuple())

    if d < 210:
        rawsql = "select a.*, security, sector, subsec, hq from ( \
                  select rn+1 rn, symbol, round(c_diff*100) c_diff from ff_stock_w5 where start_date='"+ds.strftime("%Y-%m-%d")+"' and end_date='"+de.strftime("%Y-%m-%d")+"' and symbol='"+ss+"' \
                  ) a, ff_scan_symbols b where a.symbol=b.symbol order by rn"
    else:
        rawsql = "select a.*, security, sector, subsec, hq from ( \
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