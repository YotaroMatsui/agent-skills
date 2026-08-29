# agent-skills

自作のAgent Skillを公開するリポジトリです。
現在は `layered-japanese-writing` のみを収録しています。

## layered-japanese-writing

日本語の説明文・技術文書を、境界付き完全性、抽象階層、依存関係の閉包、局所的な情報量の観点から設計・執筆・校正するSkillです。

表記上の誤りだけを直すのではなく、対象読者、目的、対象範囲を定め、必要な知識へ到達できる文章構造を作ります。

## インストール

Skillの一覧を確認します。

```bash
npx skills add YotaroMatsui/agent-skills --list
```

指定したSkillをCodexへインストールします。

```bash
npx skills add YotaroMatsui/agent-skills \
  --skill layered-japanese-writing \
  -a codex
```

グローバルにインストールする場合は次を実行します。

```bash
npx skills add YotaroMatsui/agent-skills \
  --skill layered-japanese-writing \
  -a codex \
  -g
```

固定版を利用する場合は、公開済みのGit tagを指定します。次は`v0.1.0`公開後の例です。

```bash
npx skills@1.5.23 add 'YotaroMatsui/agent-skills#v0.1.0' \
  --skill layered-japanese-writing \
  -a codex
```

## ALPS適合と版管理

Vercel Skills CLI（`npx skills`）は、Skillの発見、配布、およびインストール手段です。
CLIでの一覧表示やインストールの成功は、ALPS適合、独立認証、正式採用、または有効性を証明しません。

`layered-japanese-writing`の「ALPS準拠。」は、Skill Descriptionだけを対象とするALPS v0.5.0 12.1のDescription Conformance（PFおよびALPS 4–6）の簡略主張です。
Skill Package、記述されたProcessのProcess Conformance、および個別Process InstanceのExecution Conformanceは主張範囲に含みません。
現在の管理状態はcandidate（試行利用）であり、VAL-001とVAL-002は未評価です。

`main`は可変です。
再現可能な固定版は、merge後に作成し、以後移動または再利用しないGit tagで識別し、対応するGitHub Releaseに検証結果と既知の未評価事項を記録します。

## 構成

Skill本体は `skills/layered-japanese-writing/` にあります。
`SKILL.md` を入口とし、lintスクリプト、設定、評価規準、調査根拠、ALPSの検証・管理記録、およびMIT noticeを同じパッケージに保持します。

## License

[MIT License](./LICENSE)
