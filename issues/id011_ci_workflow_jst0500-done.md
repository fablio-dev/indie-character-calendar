# タイトル: GitHub Actions ワークフロー作成（JST 05:00）

- ID: `id011`
- ステータス: `done`
- モデル: CODEX

## 目的/期待成果
- スケジュール実行と手動実行、`contents: write` 権限を備えたCIを整備。

## 読み込むべきファイル
- `AGENTS.md`
- `.github/workflows/update.yml`（予定）

## 関連仕様の抜粋
- AGENTS.md > GitHub Actions 雛形

## 作業内容
- `update.yml` を追加し、スケジュール/dispatch/TZ 設定を反映。

## 実行/検証コマンド
- GitHub 上でワークフローのlint/可視確認

## 変更予定/非対象
- 変更: `.github/workflows/update.yml`
- 非対象: アプリ本体

## Definition of Done
- 手動実行が可能で、スケジュールが 05:00 JST 相当で設定されている。

## リスク/注意点
- `permissions: contents: write` を忘れない。
