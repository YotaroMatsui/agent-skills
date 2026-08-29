# Skill検証記録

- 対象Skill・版: `layered-japanese-writing` 0.1.0
- 検証範囲: Skill DescriptionおよびSkill Package
- Conformance対象: 記述
- Conformance形態: 該当なし
- Conformance基準: ALPS 12.1 a)に基づく箇条4から6の記述適合、およびPackageを対象とする5.7。
- 適用規範・Control: ALPS、Process Framework、Codex Skill Creator、ユーザーが提示した知識完全性・再帰性・抽象階層・情報量の構想、日本語技術文書規範。
- レビュー基準: Name、Purpose、Outcomeの単一性と整合、Taskの行為性と規範属性、一般Skillの方法非依存性、発見層と実行層の整合、付随資源の役割、参照解決、代表文脈でのOutcome達成可能性。
- 独立した観点: ALPS同梱の機械的事前検査、決定的unit test、およびfixtureの期待値を用いた。独立した人間または別LLMによるforward testは未実施である。
- 代表的利用文脈: 概念密度の高い日本語解説、Markdownの構造校正、表層規則の安全な修正、構造上の欠陥を含む原稿。
- 境界事例: 一段落で完結する短い操作説明、コードフェンス・URL・引用・frontmatter、短い内部フェンス、文書先頭の水平線。

## 結果

| 検証項目 | 証拠 | 判定 | 欠陥ID |
|---|---|---|---|
| 発見層が作業、適用状況、判定情報を示し、`ALPS準拠。`で終わる | `SKILL.md` frontmatter、ALPS checker | 適合 | なし |
| Name、Purpose、Outcomeが役割を分け、PurposeをOutcomeが充足する | `SKILL.md`、`traceability.md` | 適合 | なし |
| 各Taskが個別行為と規範属性を持つ | K1からV6の手動レビュー、ALPS checker | 適合 | なし |
| 規範部分が特定のツール、固定閾値、実行順序を一般要件にしない | Constraints、Enablers、Common Approachの手動レビュー | 適合 | なし |
| TaskとOutcomeを追跡できる | `traceability.md` | 適合 | なし |
| 正本のSkill Descriptionが一つで、付随資源の役割と利用条件が識別できる | `SKILL.md` Bundled Resources、相対リンク検査 | 適合 | なし |
| Skill Creatorのfrontmatter、命名、placeholder条件を満たす | Ruby YAML解析、名称・長さ・文字種検査、`rg`によるplaceholder検査 | 適合 | ENV-001 |
| lintが構造、保護領域、情報量、outline、autofix、Markdown異常を再現可能に扱う | `python3 -m unittest discover -s tests -v`: 9件成功 | 適合 | TST-001（処置済み） |
| 良好fixtureと短文境界事例を過剰検出しない | `layered-good.md`と`short-boundary.md`: error、warning、suggestion各0件 | 適合 | なし |
| 問題fixtureから期待する構造・表層所見を得る | `problematic.md`: error 1件、warning 1件、suggestion 3件 | 適合 | なし |
| 概念解説を見出しと主題文の木へ投影できる | `outline layered-good.md`、`test_outline_keeps_heading_tree` | 適合 | なし |
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
- 記述適合と初期Package検証は、個別文書への実行適合や外的妥当性を意味しない。

## 初期判断

記述と決定的ハーネスは、試行利用が可能な状態にある。
実読者の理解改善を含む本採用は、VAL-001とVAL-002の証拠が得られるまで条件付きとする。
