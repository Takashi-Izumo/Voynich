# 再現可能性の状態

## A. 元資料または決定論的手続きから厳密に再現できるもの

### コーパス

- A-2: 297 tokens / 195 types
- Herbal A: 7,694 / 2,270
- whole VM n-gram corpus: 37,608 / 7,457
- strict whole-VM attestation vocabulary: 37,597 / 7,455

### Table 1の観測側

- 21 complete bifolia / 84 surfaces
- 6,765 analyzed tokens
- 6,747 covered tokens
- 20,207 word-internal transitions
- forward 61.6371%
- same layer 23.2345%
- backward 15.1284%
- zero-back words 61.7163%
- zero-or-one-back words 93.4193%

50,000回randomizationはseed 30を明示して再実行し、mean 39.6494%、1件が観測値以下、plus-one tail `3.99992e-5`を得ました。

### Table 2

固定4foldの結果は印刷値まで一致します。

- Layer structure only: 27.38 / 57.14 / 22.62%
- Full seven-layer: 38.10 / 76.19 / 42.86%

### D--G exact reassignment

- 180 allocations
- observed 99
- mean 108.1666667
- one allocation at or below observed
- exact one-sided `p=1/180=0.0055556`

### exact inventory

- 430 distinct main-shelf rows
- 600 physical main-shelf tablets
- INTERNAL 294
- SECOND 146
- BOUNDARY 125, of which safety=1 is 14
- RESTART 35
- Paragraph START 8

### archived n-gram null outputs

保存済み5,000回出力からTable 4の値を直接再集計できます。

## B. 元のrandom streamが失われたため、新しい固定seedで再構築したもの

### 2,000 repeated n-gram bifolium holdouts

元の2,000 configurationとseedは保存されていません。新しいseed 20260817の2,000 configurationをCSVで保存しています。論文値との差は約0.0--0.24 percentage pointです。

### next-state prediction

元の平滑化係数とfold seedは保存されていません。パッケージではadditive smoothing `alpha=0.1`、seed 123を使用し、

- bigram 2.293238 bits/state
- trigram 2.169472 bits/state

を得ています。論文値との差はそれぞれ0.00014、0.00037 bits/stateです。

### Table 3と棚attestation

元seedは保存されていません。exact inventoryとexact scheduleを用いて新seedで再実行し、論文値と近い平均を得ています。全run CSV、percentile、seedを保存しています。

## C. 元コードを回収できず、完全再現できないもの

### 475--650枚の元整数optimizer

論文では475, 500, 525, 550, 575, 600, 625, 650枚を比較していますが、各budget inventoryを作った元のoptimization routineは回収できませんでした。

保存されているのは最終600枚inventoryです。`09_budget_sensitivity_reconstructed.py`は、600枚でexact inventoryを再現し、その周囲を明示的規則で再量子化する新しい感度分析です。元optimizerの結果として引用してはいけません。

### 元の全random seeds

Table 3、5,000回shelf attestation、2,000 holdout、next-state foldsの元seedは回収できませんでした。新seedは各summary JSONに保存されています。

## D. 新たに発見された監査結果

Appendix Aの印刷規則を文字どおり実装すると、430 distinct rows / 600 tabletsのうち、414 rows / 584 tabletsが到達可能で、16 tabletsは到達不能です。到達可能な空箱は0です。

この16枚は、元の報告値を改変せずに監査結果として別管理しています。投稿前には、元実装に未記載の初期化規則がなかったか、または16枚を「物理在庫だがstatic runでは未使用」と位置づけるかを確定する必要があります。
