#!/usr/bin/env python3
"""Sensitivity version of the D--G reassignment test using all 23 working glyphs.

The printed 99 / 108.17 result is reproduced by 07_cross_currier_reassignment.py
using the stored stable-22 definition. This script shows the corresponding result if
rare g is included in the same state inventory and strict token filtering is used.
"""
from __future__ import annotations
import argparse,csv,itertools,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from voynich_common import VM23,dump_json,load_zl3b,segment,tokens_from_text_attestation_strict
QUIRES=('D','E','F','G')
def active(words):
 out=set()
 for w in words:
  gs=segment(w,VM23)
  if gs:out.update((gs[i],gs[i+1]) for i in range(len(gs)-2))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--zl3b',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True);args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
 meta,records=load_zl3b(args.zl3b);words=defaultdict(list);lang={}
 for rec in records:
  m=rec.meta
  if m.get('Q') not in QUIRES or m.get('I')!='H' or m.get('L') not in {'A','B'}:continue
  k=(m['Q'],m['B']);lang[k]=m['L'];words[k].extend(w for w in tokens_from_text_attestation_strict(rec.text) if segment(w,VM23) is not None)
 states={k:active(v) for k,v in words.items()};A={q:set().union(*(states[k] for k in states if k[0]==q and lang[k]=='A')) for q in QUIRES};B=sorted(k for k in states if lang[k]=='B')
 obs={q:tuple(k for k in B if k[0]==q) for q in QUIRES};rows=[]
 for d in itertools.combinations(B,1):
  r1=[x for x in B if x not in d]
  for e in itertools.combinations(r1,2):
   r2=[x for x in r1 if x not in e]
   for f in itertools.combinations(r2,2):
    g=tuple(x for x in r2 if x not in f);al={'D':d,'E':e,'F':f,'G':g};per={q:len(set().union(*(states[x] for x in al[q]))-A[q]) for q in QUIRES};rows.append({'D':' '.join(f'{x[0]}:{x[1]}' for x in d),'E':' '.join(f'{x[0]}:{x[1]}' for x in e),'F':' '.join(f'{x[0]}:{x[1]}' for x in f),'G':' '.join(f'{x[0]}:{x[1]}' for x in g),'total':sum(per.values()),'observed':int(al==obs)})
 vals=np.array([r['total'] for r in rows]);observed=next(r['total'] for r in rows if r['observed'])
 summary={'definition':'VM23 including g; strict token extraction','observed':int(observed),'mean':float(vals.mean()),'minimum':int(vals.min()),'maximum':int(vals.max()),'count_le':int(np.sum(vals<=observed)),'p':float(np.mean(vals<=observed))}
 with (args.outdir/'cross_currier_VM23_180_allocations.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 dump_json(summary,args.outdir/'cross_currier_VM23_summary.json');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
