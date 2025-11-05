# タイトル: HTML→テキスト整形の実装（BeautifulSoup）

- ID: `id005`
- ステータス: `done`
- モデル: CODEX
- 完了日: 2025-11-03（JST）

## 目的/期待成果
- 不要タグ除去と本文抽出により、AI に渡すテキストを安定化させる。

## 読み込むべきファイル
- `AGENTS.md`
- `src/scrape.py`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(5) HTML取得と整形

## 作業内容
- `scrape.py` に `extract_main_text(html: str) -> str` を実装。
- ナビ・フッタ・スクリプト等の除去規則を定義。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src.scrape import fetch_html, extract_main_text; print(extract_main_text(fetch_html('https://example.com'))[:80])\nPY`

## 変更予定/非対象
- 変更: `src/scrape.py`
- 非対象: AI クライアント

## Definition of Done
- 出力テキストにスクリプト/スタイルが含まれない。

## リスク/注意点
- サイト差異に備え例外に強い設計。
