#!/usr/bin/env python3
"""A-2 unigram/bigram/trigram complete-word attestation null test.

Input: ZL3b-n.txt, Version 3b (13/05/2025).
Primary design: each run has the exact A-2 multiset of VM-glyph word lengths;
paths are sampled from unigram/bigram/trigram models conditioned on ending at
that length. Bigram/trigram END probabilities are therefore retained rather
than words being naively truncated.
Sensitivity design: each n-gram model generates its own word lengths using END.

The script reproduces the project corpora:
A-2 = 297 tokens / 195 types
Herbal A = 7,694 / 2,270
strict whole manuscript = 37,597 / 7,455
"""
import re, argparse
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

GLYPHS=['cfh','cph','cth','ckh','ch','sh','q','p','f','k','o','t','a','d','e','s','i','l','y','r','m','n','g']
GS=sorted(GLYPHS,key=len,reverse=True)
GI={g:i for i,g in enumerate(GLYPHS)}; IG={i:g for g,i in GI.items()}; G=len(GLYPHS); END=G

def segment(w):
    out=[]; i=0
    while i<len(w):
        for g in GS:
            if w.startswith(g,i): out.append(g); i+=len(g); break
        else: return None
    return out

def token_candidates(txt):
    txt=txt.replace('<%>','').replace('<$>','')
    txt=re.sub(r'<!.*?>','',txt).replace('<->','.')
    return [x for x in re.split(r'[.,\s]+',txt) if x]

def load_zl(path):
    lines=open(path,encoding='utf-8').read().splitlines()
    meta={}; rec=[]
    for line in lines:
        m=re.match(r'<([^>.]+)>\s+<!\s*(.*?)>',line)
        if m:
            meta[m.group(1)]=dict(re.findall(r'\$(\w+)=([^\s>]+)',m.group(2)))
            continue
        m=re.match(r'<([^,>]+),([^>]+)>\s+(.*)$',line)
        if m:
            locus,typ,txt=m.groups(); page=locus.split('.')[0]
            rec.append((page,locus,typ,txt))
    return meta,rec

def extract(rec,pages=None,paragraph_only=False,require23=False):
    out=[]
    for page,locus,typ,txt in rec:
        if pages is not None and page not in pages: continue
        if paragraph_only and 'P' not in typ: continue
        for w in token_candidates(txt):
            if not re.fullmatch(r'[a-z]+',w): continue
            if require23 and segment(w) is None: continue
            out.append(w)
    return out

def cdf(counts,fallback=None):
    x=np.asarray(counts,float)
    if x.sum()==0:
        x=np.asarray(fallback,float) if fallback is not None else np.ones_like(x)
    if x.sum()==0:
        x=np.ones_like(x)
    x=x/x.sum(); return np.cumsum(x)

def draw(cum,rng): return int(np.searchsorted(cum,rng.random(),side='right'))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('zl3b'); ap.add_argument('--runs',type=int,default=5000); ap.add_argument('--seed',type=int,default=20260817); ap.add_argument('--out',default='A2_null')
    args=ap.parse_args()
    meta,rec=load_zl(args.zl3b)
    a2_pages={'f2r','f2v','f7r','f7v'}
    ha_pages={p for p,m in meta.items() if m.get('I')=='H' and m.get('L')=='A'}
    a2=extract(rec,a2_pages,paragraph_only=True,require23=True)
    ha=extract(rec,ha_pages)
    vm=extract(rec,set(meta))
    assert (len(a2),len(set(a2)))==(297,195)
    assert (len(ha),len(set(ha)))==(7694,2270)
    assert (len(vm),len(set(vm)))==(37597,7455)
    A,H,V=set(a2),set(ha),set(vm)
    segs=[segment(w) for w in a2]; lens=[len(s) for s in segs]; maxL=max(lens)
    unig=np.zeros(G); start=np.zeros(G); big=np.zeros((G,G)); second=np.zeros((G,G)); tri=defaultdict(lambda:np.zeros(G))
    bigE=np.zeros((G,G+1)); triE=defaultdict(lambda:np.zeros(G+1))
    for s in segs:
        ids=[GI[g] for g in s]
        start[ids[0]]+=1
        for i in ids: unig[i]+=1
        for i in range(1,len(ids)): big[ids[i-1],ids[i]]+=1
        if len(ids)>=2: second[ids[0],ids[1]]+=1
        for i in range(2,len(ids)): tri[(ids[i-2],ids[i-1])][ids[i]]+=1
        for i in range(len(ids)-1): bigE[ids[i],ids[i+1]]+=1
        bigE[ids[-1],END]+=1
        if len(ids)==1: triE[('S',ids[0])][END]+=1
        else:
            triE[('S',ids[0])][ids[1]]+=1
            for i in range(2,len(ids)): triE[(ids[i-2],ids[i-1])][ids[i]]+=1
            triE[(ids[-2],ids[-1])][END]+=1
    unig_c=cdf(unig); start_c=cdf(start,unig); start_p=start/start.sum()
    unigE=np.r_[unig,len(segs)]
    bigEp=np.zeros_like(bigE)
    for i in range(G):
        x=bigE[i] if bigE[i].sum() else unigE; bigEp[i]=x/x.sum()
    triEp={k:v/v.sum() for k,v in triE.items()}
    def tp(ctx): return triEp.get(ctx,bigEp[ctx[1]])
    # exact-length backward probabilities
    fb=np.zeros((G,maxL)); fb[:,0]=bigEp[:,END]
    for r in range(1,maxL): fb[:,r]=bigEp[:,:G]@fb[:,r-1]
    contexts=[('S',g) for g in range(G)]+[(a,b) for a in range(G) for b in range(G)]
    ft={c:np.zeros(maxL) for c in contexts}
    for c in contexts: ft[c][0]=tp(c)[END]
    for r in range(1,maxL):
        for ctx in contexts:
            p=tp(ctx); b=ctx[1]; ft[ctx][r]=sum(p[c]*ft[(b,c)][r-1] for c in range(G))
    bi_first={}; bi_next={}; tr_first={}; tr_next={}
    for L in range(1,maxL+1):
        x=start_p*fb[:,L-1]; bi_first[L]=cdf(x,start_p)
        x=np.array([start_p[c]*ft[('S',c)][L-1] for c in range(G)]); tr_first[L]=cdf(x,start_p)
    for b in range(G):
        for rem in range(1,maxL): bi_next[(b,rem)]=cdf(bigEp[b,:G]*fb[:,rem-1],bigEp[b,:G])
    for ctx in contexts:
        p=tp(ctx); b=ctx[1]
        for rem in range(1,maxL):
            x=np.array([p[c]*ft[(b,c)][rem-1] for c in range(G)])
            tr_next[(ctx,rem)]=cdf(x,p[:G])
    p_end=len(segs)/sum(lens)
    def cat(w): return 0 if w in A else 1 if w in H else 2 if w in V else 3
    def exact(model,L,rng):
        if model=='uni': ids=[draw(unig_c,rng) for _ in range(L)]
        elif model=='bi':
            ids=[draw(bi_first[L],rng)]; rem=L-1
            while rem: ids.append(draw(bi_next[(ids[-1],rem)],rng)); rem-=1
        else:
            ids=[draw(tr_first[L],rng)]; rem=L-1
            while rem:
                ctx=('S',ids[0]) if len(ids)==1 else (ids[-2],ids[-1]); ids.append(draw(tr_next[(ctx,rem)],rng)); rem-=1
        return ''.join(IG[i] for i in ids)
    def free(model,rng,maxlen=30):
        if model=='uni':
            ids=[draw(unig_c,rng)]
            while len(ids)<maxlen and rng.random()>p_end: ids.append(draw(unig_c,rng))
        elif model=='bi':
            ids=[draw(start_c,rng)]
            while len(ids)<maxlen:
                n=draw(np.cumsum(bigEp[ids[-1]]),rng)
                if n==END: break
                ids.append(n)
        else:
            ids=[draw(start_c,rng)]
            while len(ids)<maxlen:
                ctx=('S',ids[0]) if len(ids)==1 else (ids[-2],ids[-1]); n=draw(np.cumsum(tp(ctx)),rng)
                if n==END: break
                ids.append(n)
        return ''.join(IG[i] for i in ids),len(ids)
    rows=[]
    for design in ('exact','free'):
        for mi,model in enumerate(('uni','bi','tri')):
            rng=np.random.default_rng(args.seed+mi*1000+(10000 if design=='free' else 0))
            for r in range(args.runs):
                cc=np.zeros(4,int); wc=Counter(); ll=[]
                if design=='exact':
                    words=[exact(model,L,rng) for L in lens]; ll=lens
                else:
                    tmp=[free(model,rng) for _ in range(297)]; words=[x[0] for x in tmp]; ll=[x[1] for x in tmp]
                for w in words: cc[cat(w)]+=1; wc[w]+=1
                tc=np.zeros(4,int)
                for w in wc: tc[cat(w)]+=1
                rows.append(dict(design=design,model=model,run=r+1,A2=cc[0]/297,HA_out=cc[1]/297,VM_out=cc[2]/297,unattested=cc[3]/297,VM_total=(cc[:3].sum())/297,outside_A2=(cc[1]+cc[2])/297,types=len(wc),hapax=sum(v==1 for v in wc.values()),A2_type=tc[0]/len(wc),HA_type=(tc[0]+tc[1])/len(wc),VM_type=tc[:3].sum()/len(wc),mean_length=np.mean(ll),sd_length=np.std(ll)))
    df=pd.DataFrame(rows); df.to_csv(args.out+'_runs.csv',index=False)
    sm=[]
    for (d,m),g in df.groupby(['design','model']):
        for col in ['A2','HA_out','VM_out','VM_total','outside_A2','unattested','types','hapax','A2_type','HA_type','VM_type','mean_length','sd_length']:
            x=g[col].to_numpy(); sm.append(dict(design=d,model=m,metric=col,mean=x.mean(),p2_5=np.quantile(x,.025),p97_5=np.quantile(x,.975)))
    pd.DataFrame(sm).to_csv(args.out+'_summary.csv',index=False)
    print('Corpora:',len(a2),len(set(a2)),len(ha),len(set(ha)),len(vm),len(set(vm)))

if __name__=='__main__': main()
