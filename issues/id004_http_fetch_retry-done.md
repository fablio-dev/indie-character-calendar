# タイトル: HTTP 取得ユーティリティの実装（requests + リトライ）

- ID: `id004`
- ステータス: `done`
- モデル: CODEX
- 完了日: 2025-11-03（JST）

## 目的/期待成果
- タイムアウト・User-Agent・指数バックオフ対応の `fetch_html(url)` を提供する。

## 読み込むべきファイル
- `AGENTS.md`
- `src/scrape.py`
- `src/utils.py`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(3) 行ごとの処理

## 作業内容
- `utils.py` にリトライデコレータと共通 User-Agent, timeout を実装。
- `scrape.py` に `fetch_html(url: str) -> str` を実装。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src.scrape import fetch_html; print(len(fetch_html('https://example.com'))>0)\nPY`

## 変更予定/非対象
- 変更: `src/utils.py`, `src/scrape.py`
- 非対象: HTML整形/抽出ロジック

## Definition of Done
- 一般的なサイトで例外なくHTML文字列を返す。
- タイムアウト/HTTPエラーで例外が発生し、呼び出し側で捕捉可能。

## リスク/注意点
- 過度な並列化や攻撃的アクセスを避ける。
