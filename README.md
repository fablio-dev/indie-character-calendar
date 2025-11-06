# インディーキャライベントカレンダー

[インディーキャラ](https://note.com/fablio_dev/n/nd1a6a5785b1b)に出会える創作イベントのカレンダーです。（自動更新なのでおかしいところがあるかも？)

- 公開ページ: GitHub Pages（`docs/index.md` を元に自動生成予定）
- イベント一覧テーブルは `docs/index.md` に出力され、自動更新されます。

## 使い方（開発者向け説明）

### ローカル実行手順

1. Python 3.11 以上を用意します。
2. `pip install -r requirements.txt` で依存関係をインストールします。
3. `.env.example` を参考に環境変数 `GEMINI_API_KEY` を設定します（`.env` はコミットしないでください）。
4. `python -m src.main --dry-run` を実行し、差分のみを確認します。

### Secrets の取り扱い

- `GEMINI_API_KEY` は GitHub Secrets とローカル環境変数で管理し、ログやリポジトリへ出力しません。
- `.env` ファイルはバージョン管理対象外です。必要な場合は `.env.example` をコピーして使用してください。
