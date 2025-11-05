# タイトル: Gemini クライアント実装とJSON抽出

- ID: `id006`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- 既定プロンプトで JSON を返し、非JSON応答時も安全に抽出する。

## 読み込むべきファイル
- `AGENTS.md`
- `src/ai_client.py`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(4) AI 抽出

## 作業内容
- `ai_client.py` に `extract_event_info(text: str) -> dict` を実装。
- 環境変数 `GEMINI_API_KEY` を利用。タイムアウト/リトライ実装。
- JSON ブロック抽出フォールバックを実装。

## 実行/検証コマンド
- `python - <<'PY'\nfrom src.ai_client import extract_event_info\nprint(extract_event_info(''))\nPY`

## 変更予定/非対象
- 変更: `src/ai_client.py`
- 非対象: CSV 更新/Markdown 生成

## Definition of Done
- 期待スキーマの dict を返す（キー欠落時は `不明` を補完）。

## リスク/注意点
- API キーの漏洩を防ぐ（ログ抑制）。
