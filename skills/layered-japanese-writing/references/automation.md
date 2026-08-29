# 自動化ガイド

## 役割分担

自動化は三層に分ける。

1. 決定的lintは、同じ入力に同じ所見を返す。
2. 意味レビューは、依存関係、抽象度、完全性、意味保存を評価する。
3. 受入れ判断は、文書の影響度に応じて人間または権限を持つ受領者が行う。

決定的lintから意味レビューを呼び出してもよいが、両者の所見と合否を混ぜない。

## CLI

標準ライブラリだけで実行できる。

```bash
python3 scripts/ja_structure_lint.py check document.md
python3 scripts/ja_structure_lint.py check document.md --format json --fail-on warning
python3 scripts/ja_structure_lint.py outline document.md
python3 scripts/ja_structure_lint.py fix document.md --output document.fixed.md
```

`check`は、Markdownの見出し構造、段落と節の参考閾値、文体ヒューリスティック、JSONL規則を検査する。
`outline`は、見出しと各節の最初の主題候補を抽出する。
`fix`は、`autofix: true`を持つ規則だけを別ファイルへ適用する。
原稿を上書きしないため、`fix`には出力先が必要である。

## 保存時hook

保存時には、変更したMarkdownだけを`check --format json`へ渡す。
結果は、決定的所見としてエディタまたはAgentへ返す。
警告があるたびに全文を書き換える運用は避ける。
対象位置と理由を示し、必要な箇所だけを修正する。

## 停止時検査

Agentの停止前に、次の状態だけを確認する。

- hard errorが残っていないか。
- 修正した節に未評価の意味所見が残っていないか。
- 原資料との差分確認が必要な変更を完了したか。

自動修正と再検査の反復回数には上限を設ける。
同じ所見が再発した場合は停止し、規則の誤検出、相反する規則、または意味上の判断が必要かを報告する。
二回程度の反復は開始値として利用できるが、普遍的な回数ではない。

## CI

CIでは、適用先の規則セットと閾値をリポジトリに固定する。
新しい規則は、既存文書の基準線と回帰fixtureを確認してからhard errorへ昇格する。

例:

```bash
python3 scripts/ja_structure_lint.py check docs/guide.md --fail-on error
python3 -m unittest discover -s tests -v
```

既存のtextlintまたはprhがある場合、置き換えずに併用する。
表記、用語、禁則は既存ツールへ残し、本ハーネスには知識階層に関係する構造ヒューリスティックだけを追加する。

## LLM意味レビューとの接続

LLMへ渡す情報は、原資料、知識契約、対象節、構造投影、決定的所見、`review-rubric.md`に限定する。
出力は、同規準の所見形式にそろえる。

LLMには、所見を消すための全文再生成ではなく、根拠付きの最小修正を求める。
修正後は、lintの再実行と原資料との意味照合を別々に行う。

## 限界

文字数、文数、見出し深さから、知識の完全性や読者の理解を推定することはできない。
lint規則は候補箇所の探索を高速化するEnablerであり、Skill Outcomeの達成証拠の一部に限る。
