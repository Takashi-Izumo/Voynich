#!/usr/bin/env python3
"""Extract all local A-2 events supplied to the shelf-fitting stage.

This recovers the empirical fitting inputs. It does not claim to recover the lost
integer-optimization routine that converted these observations into the published
600-tablet inventory.
"""
from __future__ import annotations
import argparse,csv,json
from collections import Counter
from pathlib import Path
from voynich_common import dump_json,extract_a2_schedule,load_zl3b,segment


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--zl3b',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True);args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
 _,records=load_zl3b(args.zl3b);schedule=extract_a2_schedule(records);rows=[]
 prev_final=None
 for line in schedule:
  words=str(line['observed_tokens']).split()
  for wi,w in enumerate(words):
   gs=segment(w);L=len(gs)
   if wi==0:
    if line['start_mode']=='PARAGRAPH_START':
     rows.append({'page':line['page'],'locus':line['locus'],'paragraph':line['paragraph'],'line_in_paragraph':line['line_in_paragraph'],'word_index_in_line':wi+1,'word':w,'class':'START','state_1':'PARAGRAPH_START','state_2':'PARAGRAPH_START','output':gs[0],'depth_after_output':1,'word_length':L,'terminates':int(L==1)})
    else:
     rows.append({'page':line['page'],'locus':line['locus'],'paragraph':line['paragraph'],'line_in_paragraph':line['line_in_paragraph'],'word_index_in_line':wi+1,'word':w,'class':'RESTART','state_1':'SPACE','state_2':'SPACE','output':gs[0],'depth_after_output':1,'word_length':L,'terminates':int(L==1)})
   else:
    rows.append({'page':line['page'],'locus':line['locus'],'paragraph':line['paragraph'],'line_in_paragraph':line['line_in_paragraph'],'word_index_in_line':wi+1,'word':w,'class':'BOUNDARY','state_1':prev_final,'state_2':'SPACE','output':gs[0],'depth_after_output':1,'word_length':L,'terminates':int(L==1)})
   if L>=2:
    rows.append({'page':line['page'],'locus':line['locus'],'paragraph':line['paragraph'],'line_in_paragraph':line['line_in_paragraph'],'word_index_in_line':wi+1,'word':w,'class':'SECOND','state_1':'SPACE','state_2':gs[0],'output':gs[1],'depth_after_output':2,'word_length':L,'terminates':int(L==2)})
   for pos in range(2,L):
    rows.append({'page':line['page'],'locus':line['locus'],'paragraph':line['paragraph'],'line_in_paragraph':line['line_in_paragraph'],'word_index_in_line':wi+1,'word':w,'class':'INTERNAL','state_1':gs[pos-2],'state_2':gs[pos-1],'output':gs[pos],'depth_after_output':pos+1,'word_length':L,'terminates':int(pos==L-1)})
   prev_final=gs[-1]
  # layout restart suppresses prev_final for the next line, but retain it only for audit
  if line is not schedule[-1]: pass
 fields=list(rows[0]);
 with (args.outdir/'A2_empirical_fitting_events.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 counts=Counter(r['class'] for r in rows)
 summary={'events':len(rows),'class_counts':dict(counts),'expected_counts':{'START':8,'RESTART':32,'BOUNDARY':257,'SECOND':283,'INTERNAL':604},'words':297,'lines':40,'paragraphs':8}
 # Aggregate state/output/depth/stop observations.
 agg=Counter((r['class'],r['state_1'],r['state_2'],r['output'],r['depth_after_output'],r['terminates']) for r in rows)
 ar=[]
 for k,n in sorted(agg.items()):ar.append({'class':k[0],'state_1':k[1],'state_2':k[2],'output':k[3],'depth_after_output':k[4],'terminates':k[5],'count':n})
 with (args.outdir/'A2_empirical_fitting_events_aggregated.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(ar[0]));w.writeheader();w.writerows(ar)
 dump_json(summary,args.outdir/'A2_empirical_fitting_events_summary.json');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
