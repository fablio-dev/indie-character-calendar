# タイトル: README に自動生成テーブル用マーカーを挿入

- ID: `id003`
- ステータス: `done`
- モデル: CODEX
- 完了日: 2025-11-03（JST）

## 目的/期待成果
- 自動生成範囲を明確にし、人手編集部分を保護する。

## 読み込むべきファイル
- `AGENTS.md`
- `README.md`（存在すれば）

## 関連仕様の抜粋
- AGENTS.md > README のマーカー運用

## 作業内容
- `README.md` が無ければ新規作成。
- 以下のコメントマーカーを追加：
  `<!-- events:table:start -->` と `<!-- events:table:end -->`
- マーカー間には説明用の一行コメントを入れる。

## 実行/検証コマンド
- `rg "events:table:start|events:table:end" README.md`

## 変更予定/非対象
- 変更: `README.md`
- 非対象: マーカー外の自動編集

## Definition of Done
- README に2つのマーカーが存在する。

## リスク/注意点
- マーカーはユニークで重複させない。
