"""Auditable lexical retrieval: BM25, TF-IDF cosine, reciprocal rank fusion.
No embedding model or semantic retrieval is claimed in this baseline.
"""
import math
import re
from collections import Counter

STOP = {'的','了','是','在','和','与','如何','什么','可以','怎么','哪些','一个','我们','the','a','is','to','of','and'}

def tokens(text):
    result = []
    for run in re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]+', text.lower()):
        if re.fullmatch(r'[\u4e00-\u9fff]+', run):
            # Chinese bigrams avoid introducing a heavyweight tokenizer dependency.
            result.extend(run[i:i+2] for i in range(len(run)-1) if run[i:i+2] not in STOP)
            if len(run) == 1 and run not in STOP:
                result.append(run)
        elif run not in STOP:
            result.append(run)
    return result

def chunks(text, size=420, overlap=80):
    text = text.strip()
    if not text:
        return []
    out = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            split = max(text.rfind('\n', start + size//2, end), text.rfind('。', start + size//2, end))
            if split >= start + size//2:
                end = split + 1
        out.append({'text':text[start:end], 'start':start, 'end':end})
        if end == len(text):
            break
        start = end - overlap
    return out

def search(documents, query, method='hybrid', top_k=4):
    rows = []
    for doc in documents:
        for i, chunk in enumerate(chunks(doc['text'])):
            rows.append(dict(chunk, doc_id=doc['id'], title=doc['title'], chunk_id=i+1))
    if not rows:
        return []
    counts = [Counter(tokens(row['title']+' '+row['text'])) for row in rows]
    query_count = Counter(tokens(query))
    if not query_count:
        return []
    df = Counter(t for c in counts for t in c)
    n = len(rows)
    lengths = [sum(c.values()) for c in counts]
    avg = max(sum(lengths)/n, 1)
    idf = {t: math.log((n+1)/(f+1))+1 for t,f in df.items()}
    qv = {t:(1+math.log(v))*idf[t] for t,v in query_count.items() if t in idf}
    qnorm = math.sqrt(sum(v*v for v in qv.values())) or 1
    bm, cosine = [], []
    for c,length in zip(counts,lengths):
        bm.append(sum(math.log(1+(n-df[t]+.5)/(df[t]+.5))*c[t]*2.5/(c[t]+1.5*(.25+.75*length/avg)) for t in query_count if c[t]))
        vec = {t:(1+math.log(v))*idf[t] for t,v in c.items()}
        norm = math.sqrt(sum(v*v for v in vec.values())) or 1
        cosine.append(sum(qv.get(t,0)*v for t,v in vec.items())/(qnorm*norm))
    if method == 'bm25':
        scores = bm
    elif method == 'tfidf':
        scores = cosine
    else:
        scores = [0.0]*n
        for values in (bm,cosine):
            for rank,i in enumerate(sorted(range(n),key=lambda j:values[j],reverse=True),1):
                if values[i]>0:
                    scores[i] += 1/(60+rank)
    result=[]
    for i in sorted(range(n),key=lambda j:scores[j],reverse=True):
        if scores[i] <= 0 or len(result)>=top_k:
            continue
        result.append(dict(rows[i], score=round(scores[i],6), bm25=round(bm[i],4), cosine=round(cosine[i],4)))
    return result
