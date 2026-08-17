#!/usr/bin/env python3
"""Exact 180-allocation D--G mixed-quire active-compartment reassignment test.

This follows the stored analysis definition that reproduces the paper exactly:
stable 22 glyphs (the 23-character inventory excluding rare g) and a pair state
[a,b] is active only when it is followed by an observed next glyph in a word.
"""
from __future__ import annotations
import argparse,csv,itertools,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from voynich_common import VM23,dump_json,extract_tokens,load_zl3b,segment
STABLE22=set(VM23)-{'g'};QUIRES=('D','E','F','G')

def active_states(words):
 s=set()
 for w in words:
  gs=segment(w)
  if not gs or any(g not in STABLE22 for g in gs):continue
  s.update((gs[i],gs[i+1]) for i in range(len(gs)-2))
 return s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--zl3b',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True);args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
 meta,records=load_zl3b(args.zl3b);bif=defaultdict(list)
 for p,m in meta.items():
  if m.get('Q') in QUIRES and m.get('I')=='H' and m.get('L') in {'A','B'}:bif[(m['Q'],m['B'],m['L'])].append(p)
 A=[k for k in bif if k[2]=='A'];B=sorted([k for k in bif if k[2]=='B'])
 Astate={q:set().union(*(active_states(extract_tokens(records,pages=set(bif[k]))) for k in A if k[0]==q)) for q in QUIRES}
 Bstate={k:active_states(extract_tokens(records,pages=set(bif[k]))) for k in B}
 actual_alloc={q:tuple(k for k in B if k[0]==q) for q in QUIRES}
 def statistic(alloc):return sum(len(set().union(*(Bstate[k] for k in alloc[q]))-Astate[q]) for q in QUIRES)
 rows=[]
 for d in itertools.combinations(B,1):
  rem=[x for x in B if x not in d]
  for e in itertools.combinations(rem,2):
   rem2=[x for x in rem if x not in e]
   for f in itertools.combinations(rem2,2):
    g=tuple(x for x in rem2 if x not in f);alloc={'D':tuple(d),'E':tuple(e),'F':tuple(f),'G':g}
    per={q:len(set().union(*(Bstate[k] for k in alloc[q]))-Astate[q]) for q in QUIRES};total=sum(per.values())
    rows.append({'D':' '.join(f'{x[0]}:{x[1]}' for x in alloc['D']),'E':' '.join(f'{x[0]}:{x[1]}' for x in alloc['E']),'F':' '.join(f'{x[0]}:{x[1]}' for x in alloc['F']),'G':' '.join(f'{x[0]}:{x[1]}' for x in alloc['G']),'D_new':per['D'],'E_new':per['E'],'F_new':per['F'],'G_new':per['G'],'new_active_compartments':total,'observed_allocation':int(alloc==actual_alloc)})
 vals=np.array([r['new_active_compartments'] for r in rows]);actual=statistic(actual_alloc)
 summary={'active_state_definition':'stable-22 word-internal two-glyph contexts with at least one observed following glyph','B_bifolia':[f'{q}:{b}' for q,b,_ in B],'capacity':'1|2|2|1','allocations':len(rows),'observed':actual,'reassignment_mean':float(vals.mean()),'minimum':int(vals.min()),'maximum':int(vals.max()),'count_less_or_equal_observed':int(np.sum(vals<=actual)),'one_sided_exact_p':float(np.mean(vals<=actual))}
 with (args.outdir/'cross_currier_DG_180_allocations.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 dump_json(summary,args.outdir/'cross_currier_DG_summary.json');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
