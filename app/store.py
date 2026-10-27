import json
from contextlib import contextmanager
import os
import sqlite3
import time
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SEED=json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8'))
DB=Path(os.environ.get('DATA_DIR',str(ROOT/'runtime')))/'documents.sqlite3'

@contextmanager
def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=10)
    db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, session TEXT, title TEXT, text TEXT, created REAL)')
    db.execute('DELETE FROM documents WHERE created < ?', (time.time()-86400,))
    db.commit()
    try:
        with db:
            yield db
    finally:
        db.close()

def documents(session):
    with connect() as db:
        records=db.execute('SELECT id,title,text FROM documents WHERE session=? ORDER BY created', (session,)).fetchall()
    return SEED+[dict(r) for r in records]

def add(session,title,text):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT count(*) FROM documents WHERE session=?',(session,)).fetchone()[0]>=5:
            raise ValueError('每个会话最多上传5份文档，请先清空上传。')
        if db.execute('SELECT count(*) FROM documents').fetchone()[0]>=1000:
            raise ValueError('演示服务已达到文档容量上限。')
        identifier=uuid.uuid4().hex
        db.execute('INSERT INTO documents VALUES (?,?,?,?,?)',(identifier,session,title,text,time.time()))
    return identifier

def clear(session):
    with connect() as db:
        db.execute('DELETE FROM documents WHERE session=?',(session,))
