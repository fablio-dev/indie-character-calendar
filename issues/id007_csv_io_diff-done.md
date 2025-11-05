# タイトル: CSV I/O と差分更新フローの実装

- ID: `id007`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- 読み込み→差分比較→条件付き上書き→フラグ更新を提供する。

## 読み込むべきファイル
- `AGENTS.md`
- `src/csv_io.py`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(7) CSV更新

## 作業内容
- `csv_io.py` に読み込み/書き込み/比較関数を実装。
- `last_updated` は JST ISO8601、`comment` 初期化を実装。

## 実行/検証コマンド
- `python - <<'PY'\n# unit-like check for diff logic\nPY`

## 変更予定/非対象
- 変更: `src/csv_io.py`
- 非対象: Markdown 生成

## Definition of Done
- 差分が無ければファイル未更新（idempotent）。

## リスク/注意点
- CSV の列順固定を厳守。
