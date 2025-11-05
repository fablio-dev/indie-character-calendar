# タイトル: リポジトリ初期化とスキャフォールド作成

- ID: `id001`
- ステータス: `done`
- モデル: CODEX
- 完了日: 2025-11-03（JST）

## 目的/期待成果
- 最小構成のPythonパッケージとディレクトリを作成し、後続タスクの受け皿を整備する。

## 読み込むべきファイル
- `AGENTS.md`

## 関連仕様の抜粋
- AGENTS.md > ディレクトリ構成（推奨）
- AGENTS.md > コーディング規約

## 作業内容
- `requirements.txt` を作成（`requests`, `beautifulsoup4`）。
- `src/` 配下に `main.py`, `scrape.py`, `ai_client.py`, `csv_io.py`, `markdown.py`, `utils.py` の空ファイルを作成。
- `README.md` と `events.csv` は別タスクで用意。

## 実行/検証コマンド
- `pip install -r requirements.txt`

## 変更予定/非対象
- 変更: プロジェクト直下、`src/`
- 非対象: アプリの実装ロジック

## Definition of Done
- `requirements.txt` と `src/` のファイル群が存在する。
- インストールが成功する。

## リスク/注意点
- 依存は最小限に保つ。
