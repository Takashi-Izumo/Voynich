#!/usr/bin/env python3
"""Lightweight invariant checks for the generated reproduction package."""
from __future__ import annotations
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def rows(p):
 with (ROOT/p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
 m=load('data/derived/data_manifest.json')
 assert (m['corpora']['A2']['tokens'],m['corpora']['A2']['types'])==(297,195)
 assert (m['corpora']['Herbal_A']['tokens'],m['corpora']['Herbal_A']['types'])==(7694,2270)
 assert (m['corpora']['full_VM_ngram']['tokens'],m['corpora']['full_VM_ngram']['types'])==(37608,7457)
 assert (m['corpora']['strict_VM_attestation']['tokens'],m['corpora']['strict_VM_attestation']['types'])==(37597,7455)
 assert m['A2_schedule']=={'lines':40,'paragraphs':8,'neutral_restarts':32,'tokens':297}
 assert m['inventory']['main_tablets']==600 and m['inventory']['start_tablets']==8 and m['inventory']['safety_tablets']==14
 assert m['inventory']['class_counts']=={'RESTART':35,'SECOND':146,'BOUNDARY':125,'INTERNAL':294}
 t1=load('outputs/tables/table1_seven_layer_directionality.json')
 assert t1['analyzed_word_tokens']==6765 and t1['covered_word_tokens']==6747 and t1['word_internal_transitions']==20207
 t2=load('outputs/tables/table2_seven_layer_bifolium_classification.json')
 assert round(t2['layer_structure_only']['top1']*100,2)==27.38
 assert round(t2['full_seven_layer']['top1']*100,2)==38.10
 inv=load('outputs/audits/inventory_and_reachability_summary.json')
 assert inv['physical_main_tablets']==600 and inv['reachable_empty_state_length_combinations']==0
 assert inv['reachable_physical_tablets']==584 and inv['unreachable_physical_tablets']==16
 dg=load('outputs/tables/cross_currier_DG_summary.json')
 assert dg['allocations']==180 and dg['observed']==99 and dg['count_less_or_equal_observed']==1
 fit=load('outputs/shelf/A2_shelf_fit_assessment_summary.json')
 assert fit['summary']['dead_ends']['mean']==0
 ev=load('data/derived/A2_empirical_fitting_events_summary.json')
 assert ev['events']==1184 and ev['class_counts']==ev['expected_counts']
 print('All reproducibility invariants passed.')
if __name__=='__main__':main()
