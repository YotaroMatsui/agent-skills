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

## 構成

Skill本体は `skills/layered-japanese-writing/` にあります。
`SKILL.md` を入口とし、lintスクリプト、設定、評価規準、調査根拠、およびALPSの検証記録を同じパッケージに保持します。

## License

[MIT License](./LICENSE)
