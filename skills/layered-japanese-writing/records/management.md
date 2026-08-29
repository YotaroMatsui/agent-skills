# Skill管理記録

| 項目 | 内容 |
|---|---|
| Representation名と正本 | `layered-japanese-writing` / [`SKILL.md`](../SKILL.md) |
| Representation kind | `process`（ALPS 5.1の既定） |
| 版 | 0.1.0 |
| 管理状態 | candidate（試行利用に限る）。正式採用、独立認証、および有効性確認は未実施。 |
| 固定baseline | `v0.1.0`のGit tagと対応するGitHub Release。tag作成前のcandidateは未固定とし、作成後はtagを移動または再利用しない。本ファイル自身へcommit SHAを埋め込まない。 |
| 目的と適用範囲 | 対象読者、目的、対象範囲を識別できる日本語の説明文・技術文書の設計、執筆、および構成変更を伴う校正。表記のみの修正、文学的文体模倣、根拠なしの補完は対象外。 |
| 適用条件 | `SKILL.md`のEntry Criteria、Controls、およびConstraintsを満たすこと。高影響文書では独立した意味レビューを推奨する。 |
| 発見と配布 | `SKILL.md` frontmatterを発見情報とする。Vercel Skills CLIは発見、配布、およびインストール手段であり、その成功はALPS適合、正式採用、または有効性の証拠ではない。Skill単体配布でも`LICENSE`を同梱する。 |
| 検証証拠 | [`verification.md`](verification.md)、[`traceability.md`](traceability.md)、unit tests、相対参照・frontmatter・ALPS記述の検査、およびVercel Skills CLI 1.5.23によるdiscovery/install smoke。 |
| 未解決事項 | ENV-001、VAL-001、VAL-002。VAL-001とVAL-002は未評価であり、理解改善、意味保存率、および評価者間一致は未確認。 |

## 変更・再検証・廃止条件

- `SKILL.md`の規範的意味、frontmatter、付随資源の役割、または必須参照を変える場合は、影響範囲を確認し、ALPS Definition Processで再定義・再検証してから本記録と`verification.md`を更新する。
- script、設定、規則、テスト、license同梱、配布方法、または適用するALPS baselineを変える場合は、影響するunit test、相対参照、frontmatter・ALPS記述、およびdiscovery/install smokeを再実行する。
- ニーズが消失した場合、unsafeまたはmisleadingになった場合、後継に置換された場合、または必須参照を解決できなくなった場合は廃止を判断する。廃止時は新規の発見とインストールを止め、tag、Release、検証記録、および管理記録をTraceabilityのため保持する。
