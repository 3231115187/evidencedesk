"""Run: python -m app.evaluate. Synthetic document-level regression only."""
import json
import time
from pathlib import Path
from .retrieval import search
from .store import SEED
ROOT=Path(__file__).resolve().parent.parent

def evaluate():
    cases=json.loads((ROOT/'data/evaluation.json').read_text(encoding='utf-8'))
    results=[]
    for method in ['bm25','tfidf','hybrid']:
        recall=[];rr=[];negative=[];elapsed=[];details=[]
        for c in cases:
            start=time.perf_counter()
            hits=search(SEED,c['question'],method,top_k=100)
            elapsed.append((time.perf_counter()-start)*1000)
            ids=list(dict.fromkeys(h['doc_id'] for h in hits))[:3]
            if c['relevant']:
                recall.append(len(set(ids)&set(c['relevant']))/len(set(c['relevant'])))
                rr.append(next((1/(i+1) for i,d in enumerate(ids) if d in c['relevant']),0))
            else:
                negative.append(int(not hits))
            details.append({'question':c['question'],'expected':c['relevant'],'retrieved':ids})
        results.append({'method':method,'recall_at_3':round(sum(recall)/len(recall),4),'mrr_at_3':round(sum(rr)/len(rr),4),'negative_zero_hit_rate':round(sum(negative)/len(negative),4),'mean_retrieval_ms':round(sum(elapsed)/len(elapsed),3),'details':details})
    report={'scope':'20 synthetic cases, 8 self-authored documents; regression only; not production accuracy','positive_cases':len(recall),'negative_cases':len(negative),'results':results}
    output=ROOT/'docs/evaluation_results.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in results:
        print({k:v for k,v in row.items() if k!='details'})
    print('Saved:',output)
    return report
if __name__=='__main__':
    evaluate()
