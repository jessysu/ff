# -*- coding: utf-8 -*-
"""
Created on Sat Oct  7 16:55:38 2017

@author: jsu
"""

#pip install mysqlclient
import MySQLdb
from static import DB

db = MySQLdb.connect(host=DB['host'], user=DB['user'], passwd=DB['passwd'], db=DB['db'])

def getcur():
    return db.cursor()

def dbcommit():
    db.commit()
    return True
    
def dbclose():
    db.close()
    return True


def runsql(s, p=None):
    db = MySQLdb.connect(host=DB['host'], user=DB['user'], passwd=DB['passwd'], db=DB['db'])
    cur = db.cursor()
    if p:
        cur.execute(s,p)
    else:
        cur.execute(s)
    return True

def fetch_rawsql(s):
    db = MySQLdb.connect(host=DB['host'], user=DB['user'], passwd=DB['passwd'], db=DB['db'])
    cur = db.cursor()
    cur.execute(s)
    desc = cur.description
    return [ dict(zip([col[0] for col in desc], row)) for row in cur.fetchall()]

def table_column(table):
    cur = db.cursor()
    cur.execute("SELECT GROUP_CONCAT(upper(COLUMN_NAME)) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '"+table+"'")
    return cur.fetchone()[0].split(',')

def table_exist(table):
    cur = db.cursor()
    cur.execute("SHOW TABLES LIKE '"+table+"'")
    if cur.fetchone():
        return True
    else:
        return False

