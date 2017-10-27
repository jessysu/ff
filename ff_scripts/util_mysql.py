# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 16:55:38 2017

@author: jsu
"""

#pip install mysqlclient
import MySQLdb
from static import DB

db = MySQLdb.connect(host=DB['host'], user=DB['user'], passwd=DB['passwd'], db=DB['db'], use_unicode=True, charset="utf8")
db.set_character_set('utf8')
db.cursor().execute('SET NAMES utf8;')
db.cursor().execute('SET CHARACTER SET utf8;')
db.cursor().execute('SET character_set_connection=utf8;')

cur = db.cursor()

def dbcommit():
    db.commit()
    return True
    
def dbclose():
    db.close()
    return True

def getcur():
    return db.cursor()


def runsql(s, p=None):
    if p:
        cur.execute(s,p)
    else:
        cur.execute(s)
    db.commit()
    return True

def runsqlmany(s, p):
    cur.executemany(s,p)
    db.commit()
    return True


def fetch_rawsql(s):
    cur.execute(s)
    desc = cur.description
    return [ dict(zip([col[0] for col in desc], row)) for row in cur.fetchall()]

def table_column(table):
    cur.execute("SELECT GROUP_CONCAT(upper(COLUMN_NAME)) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '"+table+"'")
    return cur.fetchone()[0].split(',')

def table_exist(table):
    cur.execute("SHOW TABLES LIKE '"+table+"'")
    if cur.fetchone():
        return True
    else:
        return False

