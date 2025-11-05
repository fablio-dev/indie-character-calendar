# タイトル: Markdown 表生成と並び替え（ハイライト含む）

- ID: `id008`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- `event_date` 基準の並び替え、非日付は末尾、更新行は太字の表文字列を生成。

## 読み込むべきファイル
- `AGENTS.md`
- `src/markdown.py`
- `README.md`
- `events.csv`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(8) Markdown生成

## 作業内容
- `markdown.py` にテーブル生成と README 内マーカー置換関数を実装。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src.csv_io import load_events\nfrom src.markdown import render_table\nrows = load_events('events.csv')\nprint(render_table(rows, highlight_timestamp='2025-11-03T18:41:45+09:00'))\nPY`

## 変更予定/非対象
- 変更: `src/markdown.py`, `README.md`
- 非対象: CSV スキーマ

## Definition of Done
- マーカー間のみが置換される。
- 並び替えルールと太字ルールが再現される。

## リスク/注意点
- ロケール差異のない日付判定（`YYYY-MM-DD` のみ）
