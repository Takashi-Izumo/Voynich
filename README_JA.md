# ヴォイニッチ棚再構成論文・再現パッケージ

このパッケージは、投稿原稿 `20260817submission.pdf` に掲載された主要なコーパス集計、七層解析、bifolium分類、次状態予測、A-2棚シミュレーション、n-gram帰無モデル、D--G再配置検定、および在庫到達可能性監査を再計算するためのコード・入力・出力をまとめたものです。

## 重要な位置づけ

本パッケージは次の三種類を明確に区別します。

1. **完全に再現できる決定論的結果／保存済み出力**
   - 使用コーパスのトークン数・語型数
   - Table 1の観測値
   - Table 2の七層bifolium分類
   - exact 600-tablet inventoryと8枚のParagraph START inventory
   - D--Gの180通り全数再配置検定
   - 保存済み5,000回n-gram null出力

2. **新たな固定seedで再実行した確率的結果**
   - 2,000回のn-gram bifolium holdout
   - page-grouped next-state prediction
   - 1,000回A-2 shelf fit assessment
   - 5,000回A-2 shelf attestation assessment

   元の乱数系列・一部の平滑化設定が保存されていなかったため、パッケージでは新しいseedと設定を明示し、論文値への近似度を監査しています。

3. **元コードを回収できなかった部分に対する透明な再構成**
   - 475--650枚の各budgetを作った元の整数最適化ルーチンは回収できませんでした。
   - `09_budget_sensitivity_reconstructed.py` は、公開済み600枚在庫を中心にした新しい明示的な再量子化です。600枚では公開在庫を厳密に再現しますが、他budgetは論文作成時の元optimizer出力ではありません。

したがって、**最終600枚棚を使ったTable 3・完全語一致率は再実行できますが、「なぜ元optimizerが600枚を選んだか」を元コードそのものから完全再現することはできません。**

## 最短の実行方法

Python 3.13環境で、パッケージのルートから実行します。

```bash
python -m pip install -r requirements.txt
python code/12_run_all.py --budget-runs 50
python code/13_verify_package.py
```

既存の5,000回null出力を使用する通常実行では、`--full-null`は不要です。nullを最初から再生成する場合のみ、次を使用します。

```bash
python code/12_run_all.py --full-null --budget-runs 50
```

nullモデルは合計多数の生成を行うため、通常実行より大幅に長くなります。

## ディレクトリ構成

```text
code/               再現用Python
  01_prepare_data.py
  02_seven_layer_analysis.py
  03_ngram_bifolium_classification.py
  04_next_state_prediction.py
  05_inventory_reachability.py
  06_a2_shelf_simulation.py
  07_cross_currier_reassignment.py
  07b_cross_currier_vm23_sensitivity.py
  08_a2_fitting_event_extraction.py
  09_budget_sensitivity_reconstructed.py
  10_a2_ngram_null_models.py
  11_build_result_comparison.py
  12_run_all.py
  13_verify_package.py
  voynich_common.py
  a2_shelf_core.py
  original_surviving/a2_ngram_null_attestation_original.py

data/raw/           原入力
  ZL3b-n_2025-05-13_snapshot.txt
  Supplementary_Table_A1_A2_600_tablet_inventory_SIMPLE_MATH.tex

data/derived/       コードで抽出したコーパス・在庫・schedule
outputs/tables/      Table 1, Table 2, n-gram分類, next-state, D--G
outputs/shelf/       A-2棚の1,000回・5,000回出力
outputs/null/        n-gram nullの保存済み5,000回出力
outputs/audits/      論文値比較・到達可能性・パッケージ検証
outputs/budget_sensitivity/  再構成したbudget感度分析
outputs/sensitivity/ 23字版D--G感度分析
tests/               軽量な不変量テスト
docs/                論文・方法対応表・留保
```

## 使用データの監査値

`01_prepare_data.py` は以下を再現します。

| コーパス | トークン | 語型 |
|---|---:|---:|
| A-2 | 297 | 195 |
| Herbal A | 7,694 | 2,270 |
| whole VM n-gram corpus | 37,608 | 7,457 |
| strict whole-VM attestation corpus | 37,597 | 7,455 |

A-2 boundary scheduleは、40行・8段落・32 neutral restarts・297語です。

## 各コードの役割

### `01_prepare_data.py`
ZL3bを監査基準で抽出し、A-2、Herbal A、全VMの語彙、A-2 boundary schedule、600+8枚在庫CSVを作成します。

### `02_seven_layer_analysis.py`
Table 1の七層方向性と50,000回randomization、Table 2のfixed four-fold bifolium分類を計算します。

### `03_ngram_bifolium_classification.py`
同じ2,000 holdout構成で2--5gramを比較します。元のholdout random streamは保存されていなかったため、新しいseedを出力とともに保存します。

### `04_next_state_prediction.py`
Herbal A 95ページを単位とするfive-fold cross-validationでbigram/trigramのbits per next stateを計算します。平滑化値とfold seedを明示しています。

### `05_inventory_reachability.py`
公開された状態更新・停止規則のもとで、600枚在庫の各札が到達可能かを全探索します。この監査により、公開規則では584枚が到達可能、16枚が到達不能であることが分かります。これは論文の元結果ではなく、投稿前に追加された新しい監査です。

### `06_a2_shelf_simulation.py`
exact 600枚在庫＋8枚START＋40行scheduleを用い、Table 3の1,000回評価および5,000回完全語attestationを再実行します。抽選はmultiplicityに比例する復元抽出です。

### `07_cross_currier_reassignment.py`
論文の99対108.17、`p=1/180`を厳密に再現します。保存資料に対応するstable-22定義を使用します。

### `07b_cross_currier_vm23_sensitivity.py`
稀な`g`を含める23字版の感度分析です。論文値そのものではありません。

### `08_a2_fitting_event_extraction.py`
A-2から棚fitへ供給された局所イベントを抽出します。元の整数optimizerそのものではありません。

### `09_budget_sensitivity_reconstructed.py`
元optimizer未保存のため、公開600枚在庫を基準にした透明な再量子化を行います。出力には必ず「reconstructed」と明記されます。

### `10_a2_ngram_null_models.py`
length-matchedおよびfree-lengthのunigram/bigram/trigram nullを生成します。保存済み5,000回結果は`outputs/null/`にあります。元の生存スクリプトは`code/original_surviving/`にも改変せず保存しています。

### `11_build_result_comparison.py`
論文記載値と再計算値を一行ずつ比較したCSVを作ります。

### `13_verify_package.py`
必須ファイル、整数不変量、主要数値、確率的結果の許容範囲を一括検証します。

## 再現状況の確認

```bash
python code/13_verify_package.py
```

現在のアーカイブでは78項目すべてが合格します。詳細は、

```text
outputs/audits/package_verification.json
outputs/audits/paper_results_comparison.csv
```

を参照してください。

## 最重要の留保

- 元の600枚optimizerコード、元の475--650 budget inventory群、元の全random seedsは回収できていません。
- したがって、確率的実験は固定した新seedで再実行し、論文値との差を明示しています。
- exact 600-tablet inventoryそのものは保存されているため、最終棚の動作・Table 3・attestation実験は再現できます。
- 公開規則からの到達可能性監査では16枚が到達不能です。正式な投稿稿では、この監査結果と元シミュレーション実装の関係を説明する必要があります。

詳細は `docs/REPRODUCIBILITY_STATUS_JA.md` を参照してください。
