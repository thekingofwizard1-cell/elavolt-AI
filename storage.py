import sqlite3
from pathlib import Path
from datetime import datetime
DB = Path('elavolt.db')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(
  telegram_id INTEGER PRIMARY KEY,
  username TEXT,
  is_premium INTEGER DEFAULT 0,
  paid_amount REAL DEFAULT 0,
  pay_method TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS usage(
  telegram_id INTEGER,
  date TEXT,
  count INTEGER DEFAULT 0,
  PRIMARY KEY(telegram_id,date)
);
CREATE TABLE IF NOT EXISTS orders(
  order_id TEXT PRIMARY KEY,
  telegram_id INTEGER,
  amount REAL,
  method TEXT,
  status TEXT,
  txid TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_bias(
  date TEXT PRIMARY KEY,
  content TEXT,
  created_at TEXT
);
'''
def _connect():
    con = sqlite3.connect(DB)
    return con

def init_db():
    con=_connect(); con.executescript(SCHEMA); con.commit(); con.close()

def upsert_user(tid, username=None):
    now=datetime.utcnow().isoformat()
    con=_connect(); cur=con.execute('SELECT telegram_id FROM users WHERE telegram_id=?',(tid,))
    if cur.fetchone():
        con.execute('UPDATE users SET username=?, updated_at=? WHERE telegram_id=?',(username,now,tid))
    else:
        con.execute('INSERT INTO users(telegram_id,username,created_at,updated_at) VALUES(?,?,?,?)',(tid,username,now,now))
    con.commit(); con.close()

def is_premium(tid):
    con=_connect(); cur=con.execute('SELECT is_premium FROM users WHERE telegram_id=?',(tid,)); r=cur.fetchone(); con.close(); return bool(r and r[0])

def set_premium(tid, amount, method):
    now=datetime.utcnow().isoformat(); con=_connect(); con.execute('UPDATE users SET is_premium=1, paid_amount=?, pay_method=?, updated_at=? WHERE telegram_id=?',(amount,method,now,tid)); con.commit(); con.close()

def increment_usage(tid):
    date=datetime.utcnow().strftime('%Y-%m-%d'); con=_connect(); cur=con.execute('SELECT count FROM usage WHERE telegram_id=? AND date=?',(tid,date)); r=cur.fetchone()
    if r:
        c=r[0]+1; con.execute('UPDATE usage SET count=? WHERE telegram_id=? AND date=?',(c,tid,date))
    else:
        c=1; con.execute('INSERT INTO usage(telegram_id,date,count) VALUES(?,?,?)',(tid,date,1))
    con.commit(); con.close(); return c

def get_usage(tid):
    date=datetime.utcnow().strftime('%Y-%m-%d'); con=_connect(); cur=con.execute('SELECT count FROM usage WHERE telegram_id=? AND date=?',(tid,date)); r=cur.fetchone(); con.close(); return int(r[0]) if r else 0

def create_order(order_id, tid, amount, method):
    now=datetime.utcnow().isoformat(); con=_connect(); con.execute('INSERT INTO orders(order_id,telegram_id,amount,method,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(order_id,tid,amount,method,'pending',now,now)); con.commit(); con.close()

def set_order_paid(order_id, txid=None):
    now=datetime.utcnow().isoformat(); con=_connect(); con.execute('UPDATE orders SET status=?, txid=?, updated_at=? WHERE order_id=?',('paid',txid,now,order_id)); con.commit(); con.close()

def get_order(order_id):
    con=_connect(); cur=con.execute('SELECT order_id,telegram_id,amount,method,status,txid FROM orders WHERE order_id=?',(order_id,)); r=cur.fetchone(); con.close(); return r

def store_daily_bias(date_str, content):
    now=datetime.utcnow().isoformat()
    con=_connect()
    con.execute('INSERT OR REPLACE INTO daily_bias(date,content,created_at) VALUES(?,?,?)',(date_str,content,now))
    con.commit(); con.close()

def get_daily_bias(date_str):
    con=_connect(); cur=con.execute('SELECT content FROM daily_bias WHERE date=?',(date_str,)); r=cur.fetchone(); con.close(); return r[0] if r else None

def list_premium_users():
    con=_connect(); cur=con.execute('SELECT telegram_id FROM users WHERE is_premium=1'); rows=cur.fetchall(); con.close(); return [r[0] for r in rows]
