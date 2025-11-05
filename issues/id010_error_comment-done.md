# タイトル: エラーハンドリングとcomment更新の統合

- ID: `id010`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- 失敗時に既存値を保持しつつ `comment` と `last_updated` を確実に更新。

## 読み込むべきファイル
- `AGENTS.md`
- `src/main.py`
- `src/csv_io.py`

## 関連仕様の抜粋
- AGENTS.md > エラーハンドリング

## 作業内容
- 失敗パスの例外握り方針と `comment` 反映を一貫化。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src import main\nfrom src.main import _process_row\n\nmain.fetch_html = lambda url: '<html></html>'\nmain.extract_main_text = lambda html: ''\nmain.extract_event_info = lambda text: {key: '不明' for key in ('event_name','event_date','location','deadline','status')}\nrow = {\n    'alias': 'test2',\n    'url': 'https://example.com',\n    'genre': '',\n    'event_name': '古い',\n    'event_date': '2025-01-01',\n    'location': 'どこか',\n    'deadline': '2024-12-01',\n    'status': '満了',\n    'last_updated': '',\n    'comment': '',\n}\n_process_row(row, '2025-11-03T10:00:00+09:00')\nPY`

## 変更予定/非対象
- 変更: `src/main.py`, `src/csv_io.py`
- 非対象: 正常系ロジック

## Definition of Done
- 失敗時も `is_csv_updated=True` かつ `comment` と `last_updated` が更新される。

## リスク/注意点
- エラー文は簡潔かつ具体的（HTTPコード等）。
