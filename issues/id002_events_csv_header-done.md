# タイトル: events.csv の新規作成（ヘッダ確定）

- ID: `id002`
- ステータス: `done`
- モデル: CODEX
- 完了日: 2025-11-03（JST）

## 目的/期待成果
- CSV スキーマを固定し、空データでも処理可能な土台を作る。

## 読み込むべきファイル
- `AGENTS.md`

## 関連仕様の抜粋
- AGENTS.md > CSV 仕様（ヘッダ順を固定）

## 作業内容
- `events.csv` をUTF-8で作成し、以下のヘッダのみを1行目に記述：
  `alias,url,event_name,event_date,location,deadline,status,last_updated,comment`

## 実行/検証コマンド
- `rg "^alias,url,event_name,event_date,location,deadline,status,last_updated,comment$" events.csv`

## 変更予定/非対象
- 変更: `events.csv`
- 非対象: データ投入（空のまま）

## Definition of Done
- 仕様通りのヘッダを持つ `events.csv` が存在する。

## リスク/注意点
- 既存ファイルがある場合はバックアップしてから上書き。
