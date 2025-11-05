# タイトル: セキュリティとドキュメント整備（Secrets/.env.example）

- ID: `id012`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- 機密情報流出リスクを低減し、利用手順を明文化する。

## 読み込むべきファイル
- `AGENTS.md`
- `README.md`

## 関連仕様の抜粋
- AGENTS.md > セキュリティ / 秘密情報

## 作業内容
- `.env.example` を追加（コメント付き）。
- README にローカル実行手順（ドライラン含む）を追記。

## 実行/検証コマンド
- なし

## 変更予定/非対象
- 変更: `.env.example`, `README.md`, `.gitignore`
- 非対象: ランタイム実装

## Definition of Done
- 秘匿設定の取り扱いがREADMEで明記されている。

## リスク/注意点
- `.env` はコミットしない。
