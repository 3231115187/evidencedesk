import json
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient
from app import store
from app.main import app, requests_window, model_answer
from app.retrieval import chunks, search

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=store.DB
        store.DB=Path(self.temp.name)/'test.sqlite3'
        requests_window.clear()
        self.client=TestClient(app)
        self.client.get('/health')
    def tearDown(self):
        self.client.close();store.DB=self.old;self.temp.cleanup()
    def test_upload_isolation_and_delete(self):
        upload=self.client.post('/api/documents',json={'title':'research.md','text':'唯一关键词 nebula42 记录实验版本。'})
        self.assertEqual(upload.status_code,201)
        identifier=upload.json()['id']
        self.assertEqual(self.client.get('/api/documents/'+identifier).status_code,200)
        with TestClient(app) as other:
            self.assertEqual(other.get('/api/documents/'+identifier).status_code,404)
        answer=self.client.post('/api/query',json={'question':'nebula42'}).json()
        self.assertEqual(answer['sources'][0]['doc_id'],identifier)
        self.client.delete('/api/documents')
        self.assertEqual(self.client.get('/api/documents/'+identifier).status_code,404)
    def test_unknown_and_invalid_query(self):
        data=self.client.post('/api/query',json={'question':'xyzqwerty987654'}).json()
        self.assertEqual(data['mode'],'no_evidence')
        self.assertEqual(data['sources'],[])
        self.assertEqual(self.client.post('/api/query',json={'question':'hi','method':'oops'}).status_code,422)
    def test_upload_limits(self):
        self.assertEqual(self.client.post('/api/documents',json={'title':'bad.pdf','text':'abc'}).status_code,400)
        self.assertEqual(self.client.post('/api/documents',json={'title':'a.md','text':' '*10}).status_code,400)
        self.assertEqual(self.client.post('/api/documents',json={'title':'a.md','text':'a'*50001}).status_code,422)
        for _ in range(5):
            self.assertEqual(self.client.post('/api/documents',json={'title':'a.md','text':'hello'}).status_code,201)
        self.assertEqual(self.client.post('/api/documents',json={'title':'a.md','text':'hello'}).status_code,409)
    def test_body_and_cross_origin_limits(self):
        self.assertEqual(self.client.post('/api/query',content='x'*350001).status_code,413)
        self.assertEqual(self.client.post('/api/query',json={'question':'hello'},headers={'Origin':'https://evil.example'}).status_code,403)
    def test_chunk_offsets_and_coverage(self):
        text='0123456789'*200
        rows=chunks(text)
        self.assertEqual(rows[0]['start'],0)
        self.assertEqual(rows[-1]['end'],len(text))
        for r in rows:self.assertEqual(r['text'],text[r['start']:r['end']])
        for a,b in zip(rows,rows[1:]):self.assertEqual(a['end']-b['start'],80)
    def test_retrieval_and_citations(self):
        for method in ('bm25','tfidf','hybrid'):
            results=search(store.SEED,'Macro-F1和Micro-F1有什么区别？',method)
            self.assertEqual(results[0]['doc_id'],'metric')
        result=self.client.post('/api/query',json={'question':'Macro-F1'}).json()
        for source in result['sources']:
            original=next(d['text'] for d in store.SEED if d['id']==source['doc_id'])
            self.assertEqual(source['text'],original[source['start']:source['end']])
    def test_model_auth_and_fallback(self):
        env={'LLM_BASE_URL':'https://example.invalid/v1','LLM_MODEL':'test','LLM_API_KEY':'fake','DEMO_ACCESS_TOKEN':'correct'}
        with patch.dict(os.environ,env):
            self.assertEqual(self.client.post('/api/query',json={'question':'Macro-F1','use_llm':True}).status_code,403)
            with patch('app.main.model_answer',side_effect=TimeoutError):
                r=self.client.post('/api/query',json={'question':'Macro-F1','use_llm':True},headers={'X-Demo-Token':'correct'}).json()
                self.assertEqual(r['mode'],'extractive');self.assertTrue(r['warning'])
            with patch('app.main.model_answer',return_value='指标说明 [1]'):
                r=self.client.post('/api/query',json={'question':'Macro-F1','use_llm':True},headers={'X-Demo-Token':'correct'}).json()
                self.assertEqual(r['mode'],'generated')
    def test_expired_document_cleanup(self):
        self.client.post('/api/documents',json={'title':'old.md','text':'old'})
        with store.connect() as db:db.execute('UPDATE documents SET created=0')
        self.assertEqual(len(self.client.get('/api/documents').json()['documents']),len(store.SEED))
    def test_health_home_and_session(self):
        r=self.client.get('/')
        self.assertEqual(r.status_code,200)
        self.assertIn('EvidenceDesk',r.text)
        self.assertIn('frame-ancestors',r.headers['Content-Security-Policy'])
        self.assertEqual(len(self.client.cookies['evidence_session']),64)
    def test_model_citation_validation(self):
        class Response:
            def __init__(self,text):self.text=text
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,*a):return json.dumps({'choices':[{'message':{'content':self.text}}]}).encode()
        hits=search(store.SEED,'Macro-F1')
        env={'LLM_BASE_URL':'https://example.invalid/v1','LLM_MODEL':'test','LLM_API_KEY':'fake'}
        with patch.dict(os.environ,env),patch('app.main.build_opener') as opener:
            opener.return_value.open.return_value=Response('answer [99]')
            with self.assertRaises(ValueError):model_answer('test',hits)
            opener.return_value.open.return_value=Response('answer [1]')
            self.assertEqual(model_answer('test',hits),'answer [1]')
if __name__=='__main__':unittest.main()
