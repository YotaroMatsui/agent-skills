# Skill検証記録

- 対象Skill・版: `layered-japanese-writing` 0.1.0
- 検証範囲: Skill Description、およびConformance主張と分離したSkill Package検査
- Conformance主張の対象: Skill Descriptionのみ
- Conformance主張の種類: Description Conformance（自己評価）
- Conformance基準: ALPS v0.5.0 12.1のDescription Conformance（PFおよびALPS 4–6）
- Skill Package検査基準: ALPS v0.5.0 5.5
- Process ConformanceおよびExecution Conformance: 評価対象外
- 適用規範・Control: ALPS、Process Framework、Codex Skill Creator、ユーザーが提示した知識完全性・再帰性・抽象階層・情報量の構想、日本語技術文書規範。
- レビュー基準: Name、Purpose、Outcomeの単一性と整合、Taskの行為性と規範属性、一般Skillの方法非依存性、発見層と実行層の整合、付随資源の役割、参照解決、代表文脈でのOutcome達成可能性。
- 評価主体と独立性: 保守者による自己評価と自動テストを用いた。独立認証ではなく、独立した人間または別LLMによるforward testは未実施である。
- 代表的利用文脈: 概念密度の高い日本語解説、Markdownの構造校正、表層規則の安全な修正、構造上の欠陥を含む原稿。
- 境界事例: 一段落で完結する短い操作説明、コードフェンス・URL・引用・frontmatter、短い内部フェンス、文書先頭の水平線。

## 結果

| 検証項目 | 証拠 | 確認結果 | 欠陥ID |
|---|---|---|---|
| 発見層が作業、適用状況、判定情報を示し、`ALPS準拠。`で終わる | `SKILL.md` frontmatter、`test_skill_frontmatter_and_alps_claim` | 確認済み | なし |
| Name、Purpose、Outcomeが役割を分け、PurposeをOutcomeが充足する | `SKILL.md`、`traceability.md` | 確認済み | なし |
| 各Taskが個別行為と規範属性を持つ | K1からV6の手動レビュー | 確認済み | なし |
| 規範部分が特定のツール、固定閾値、実行順序を一般要件にしない | Constraints、Enablers、Common Approachの手動レビュー | 確認済み | なし |
| TaskとOutcomeを追跡できる | `traceability.md` | 確認済み | なし |
| 正本のSkill Descriptionが一つで、付随資源の役割と利用条件が識別できる | `SKILL.md` Bundled Resources、`test_relative_markdown_links_resolve`、Vercel Skills CLI copy smoke | 確認済み | なし |
| Skill Creatorのfrontmatter、命名、placeholder条件を満たす | `test_skill_frontmatter_and_alps_claim`、Vercel Skills CLI discovery smoke | 確認済み | ENV-001 |
| lintが構造、保護領域、情報量、outline、autofix、Markdown異常を再現可能に扱う | `python3 -m unittest discover -s tests -v`: 12件成功 | 確認済み | TST-001（処置済み） |
| 良好fixtureと短文境界事例を過剰検出しない | `layered-good.md`と`short-boundary.md`: error、warning、suggestion各0件 | 確認済み | なし |
| 問題fixtureから期待する構造・表層所見を得る | `problematic.md`: error 1件、warning 1件、suggestion 3件 | 確認済み | なし |
| 概念解説を見出しと主題文の木へ投影できる | `outline layered-good.md`、`test_outline_keeps_heading_tree` | 確認済み | なし |
| 実読者の理解時間と回答精度が改善する | 実読者試験を未実施 | 未評価 | VAL-001 |
| 意味レビューの評価者間一致と意味保存率 | 独立評価を未実施 | 未評価 | VAL-002 |

## 欠陥処置

| 欠陥ID | 内容 | 影響 | 対応 | 完了条件 | 期限 | 状態 |
|---|---|---|---|---|---|---|
| TST-001 | 動的importしたmoduleを`sys.modules`へ登録せず、unit testの収集が失敗した | 検証を実行できない | test loaderで登録してからmoduleを実行するよう修正 | 全unit test成功 | 完了 | 完了 |
| ENV-001 | Skill Creator同梱`quick_validate.py`の実行環境にPyYAMLがなく、公式validatorを直接実行できない | 公式validatorの実行証拠が得られない | 同validatorの条件を、Ruby YAML解析、名称・長さ・文字種検査、placeholder検査で個別確認した | PyYAMLのある環境で公式validatorを再実行 | 保留 | 保留 |
| VAL-001 | 実読者による課題達成ベンチマークがない | 認知負荷低減の外的妥当性を主張できない | `references/evaluation.md`に比較条件と指標を定義した | 対象読者を用いたpairwise試験で回答精度と時間を測定 | 保留 | 保留 |
| VAL-002 | 独立した意味レビューと評価者間一致のデータがない | 非決定的Outcomeの再現性が未確認 | R1からR8の規準と所見schemaを定義した | 複数評価者による意味保存・構造評価を実施 | 保留 | 保留 |

## 制限・前提

- 「認知負荷が低い」は、読者の心理状態を直接測定した結果ではなく、知識依存と局所情報量を管理する設計目標である。
- 420文字、4文、1800文字、7段落などの既定値は、初期の候補箇所を得るための参考閾値であり、品質標準ではない。
- JSONLの表層規則は初期例に限り、運用前に対象コーパスでprecisionとrecallを測る必要がある。
- ja-lint紹介からは構成上の着想だけを採用し、公開実装または再現可能な性能値を利用していない。
- Description Conformanceの自己評価とSkill Package検査は、独立認証、Process Conformance、Execution Conformance、正式採用、Outcome達成、または外的妥当性を意味しない。

## 初期判断

本Representationの管理状態はcandidateであり、利用は試行に限る。
正式採用は未決定である。
VAL-001とVAL-002は未評価であり、実読者の理解改善、意味保存率、および評価者間一致を含む有効性は未確認である。
