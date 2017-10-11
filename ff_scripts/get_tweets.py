# -*- coding: utf-8 -*-
"""
Created on Tue Oct  10 22:35:38 2017

@author: jsu
"""

#pip intsll twitter
import twitter
#pip install newspaper3k
from newspaper import Article

import re, sys, datetime, time

from dateutil import parser
from util_mysql import table_exist, runsql, fetch_rawsql, dbcommit, dbclose
from get_sp500 import refresh_sp500

from static import TApp
t = twitter.Twitter(
        auth=twitter.OAuth(
            TApp['token'], 
            TApp['token_secret'], 
            TApp['consumer_key'], 
            TApp['consumer_secret']))


re_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
re_tag     = re.compile(r'<[^>]+>')



FF_TWEETS_DDL = """create table ff_tweets (
symbol varchar(10),
tid bigint, 
created_at datetime, 
last_updated datetime, 
favorites int, 
retweets int,
tweet_text varchar(255),
tweet_url varchar(255),
user_name varchar(255),
user_screen varchar(255),
user_followers int,
user_friends int,
user_statuses int,
article_title varchar(1000),
article_url varchar(1000),
article text
)
""".replace('\n', ' ').replace('\r', '')

def assure_required_tables():
    if not table_exist("ff_tweets"):
        runsql(FF_TWEETS_DDL)
    if not table_exist("ff_scan_symbols"):
        refresh_sp500()
    r = fetch_rawsql("select min(datediff(now(),last_updated)) d from ff_scan_symbols")[0]
    if r['d'] > 7:
        refresh_sp500()



# Start of task
assure_required_tables()

symbols = fetch_rawsql("select symbol from ff_scan_symbols where datediff(now(),last_updated) < 60 and TIMESTAMPDIFF(minute, last_scanned, now()) > 1440 order by last_scanned desc")
if len(symbols) == 0 :
    sys.exit()

symbol = symbols['symbol']
sid = 0
current_time = datetime.datetime.now(datetime.timezone.utc)
#current_time = datetime.datetime.now()

runsql("update ff_scan_symbols set last_scaned=now() where symbol = '"+symbol+"'")
dbcommit

for d in range(6, 0, -1):
    dt = current_time - datetime.timedelta(days=d)
    tq = t.search.tweets(q="$"+symbol, lang="en", result_type="popular", until=dt.date().isoformat(), since_id=sid, count="100")
    for tw in tq['statuses']:
        sid = max(sid, tw['id'])
        td = parser.parse(tw['created_at'])
        url_list = [i['url'] for i in tw['entities']['urls']]
        if len(url_list) == 0:
            continue
        