# タイトル: メインオーケストレーター実装（--dry-run/ログ/JST）

- ID: `id009`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- 仕様どおりの一連フローを `python -m src.main` で実行可能にする。

## 読み込むべきファイル
- `AGENTS.md`
- `src/main.py`
- `src/*`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー 全体

## 作業内容
- `--dry-run` オプションでファイル未更新のプレビューを実装。
- ログ出力（INFO/DEBUG）と JST 時刻処理を実装。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src import main\nfrom src.main import _process_row\n\nmain.fetch_html = lambda url: '<html><body><p>dummy</p></body></html>'\nmain.extract_main_text = lambda html: 'Example text'\nmain.extract_event_info = lambda text: {\n    'event_name': 'テストイベント',\n    'event_date': '2025-12-31',\n    'location': 'テスト会場',\n    'deadline': '2025-12-01',\n    'status': '受付中',\n}\nrow = {\n    'alias': 'test',\n    'url': 'https://example.com',\n    'genre': '',\n    'event_name': '古いイベント',\n    'event_date': '不明',\n    'location': '不明',\n    'deadline': '不明',\n    'status': '不明',\n    'last_updated': '',\n    'comment': '古いコメント',\n}\n_process_row(row, '2025-11-03T10:00:00+09:00')\nPY`

## 変更予定/非対象
- 変更: `src/main.py`
- 非対象: スキーマ/マーカー仕様

## Definition of Done
- ドライランで処理計画が表示される。
- 非ドライランで差分時のみ CSV/README が更新される。

## リスク/注意点
- 例外は握りつぶさず上位に連ねてログ化。
