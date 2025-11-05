# AGENTS.md — auto-event-calendar

このファイルは、本リポジトリ配下の全ディレクトリに対して有効です。ここに記載の指示・規約は、エージェントおよびメンテナがこのリポジトリで作業する際の唯一の参照点です。より深い階層に別の AGENTS.md がある場合は、そちらが優先されます。

## 目的

`events.csv` に定義されたイベント一覧を基に、各公式サイトを定期的に巡回（スクレイピング）し、Google Gemini API を用いて最新情報（開催日、場所、締切、応募状況）を抽出・正規化して `events.csv` と `README.md` を自動更新します。

この文書は、以下の仕様（改訂版）をそのまま可視化・運用可能な形に落とした「実装・運用上の作業規約」です。

## スコープと優先順位

- 本 AGENTS.md は本リポジトリ全体に適用されます。
- ここに記載の「MUST/SHOULD」要件は、コード・設定・ドキュメントすべてに対して拘束力があります。
- 仕様の拡張は歓迎しますが、既存の振る舞いを壊さないこと（後方互換）。

## タスク管理（`issues/` ディレクトリ）

- 本プロジェクトのタスクは、リポジトリ直下の `issues/` ディレクトリ内で管理する（MUST）。
- 各タスクは Markdown ファイル 1 枚で表現し、ファイル名は `issues/idNNN_<slug>.md`（`NNN` は 001 からのゼロ埋め連番、`slug` は英字小文字+数字+アンダースコア）とする（MUST）。
- タスクを完了したら、同じファイルを `issues/idNNN_<slug>-done.md` にリネームし、ステータスを `done` に更新する（MUST）。
- issue ファイルの本文には少なくとも以下を含め、必要なコンテキストを自足させる（MUST）。
  - タイトル行（`# タイトル: ...`）
  - ID（`idNNN` 形式）、ステータス、モデル
  - 目的/期待成果（1〜2 行）
  - 読み込むべきファイル/ディレクトリの箇条書き
  - 関連仕様の抜粋（本 `AGENTS.md` の参照節）
  - 作業内容（3〜5 行程度）
  - 実行/検証コマンド
  - 変更予定/非対象
  - Definition of Done
  - リスク/注意点
- 進行中のタスクを新規登録する場合は、`issues/` にファイルを追加した上で最新の仕様に即した内容へ更新する（MUST）。
- `kanban/vk-tasks.md` に記載されていた旧タスクは参照用アーカイブであり、更新は不要（SHOULD NOT）。必要な情報は各 issue ファイルへ転記すること。

### issue ファイル記述テンプレート（参考）

```
# タイトル: <短い動詞で開始>

- ID: `idNNN`
- ステータス: `open|in-progress|blocked|done`
- モデル: CODEX

## 目的/期待成果
- <1-2行で要約>

## 読み込むべきファイル
- `AGENTS.md`
- `src/main.py`
- `src/markdown.py:1`

## 関連仕様の抜粋
- AGENTS.md > 処理フロー(7) README 生成

## 作業内容
- <やることを3〜5行で>

## 実行/検証コマンド
- `python -m src.main --dry-run`

## 変更予定/非対象
- 変更: `src/markdown.py`
- 非対象: 既存CSVスキーマ

## Definition of Done
- マーカー範囲のみ置換される
- 日付ソート規則を満たす
- 新規更新行が太字で表示される

## リスク/注意点
- 大規模ファイルのI/Oを避ける
```

## 実行環境・使用技術（固定）

- 実行: GitHub Actions（スケジュール + 手動 `workflow_dispatch`）
- 言語: Python
- 取得: `requests` + `beautifulsoup4`
- 抽出: Google Gemini API
- データ: `events.csv`（UTF-8）
- 出力: `README.md`（指定範囲のみ置換）

## ディレクトリ構成（推奨）

```
.
├── AGENTS.md                 # 本ファイル
├── events.csv                # データストア（UTF-8）
├── README.md                 # 一覧表をマーカー間に自動埋め込み
├── requirements.txt          # requests, beautifulsoup4 等
├── src/
│   ├── main.py               # エントリーポイント（CLI）
│   ├── scrape.py             # HTML取得・整形
│   ├── ai_client.py          # Gemini API 呼び出し
│   ├── csv_io.py             # CSV 読み書き・差分管理
│   ├── markdown.py           # 表生成と README 置換
│   └── utils.py              # 共通: 日付正規化/ログ/リトライ
└── .github/
    └── workflows/
        └── update.yml        # GitHub Actions ワークフロー
```

ディレクトリ名・ファイル名は変更可ですが、役割分離は維持してください。

## CSV 仕様（ヘッダ順を固定）

ファイル: `events.csv`（UTF-8, ヘッダあり）。以下のカラムをこの順序で保持します。

1. イベントエイリアス `alias`（手動・必須・一意）
2. URL `url`（公式サイト。空なら処理スキップ）
3. イベント名 `event_name`（AI抽出）
4. 開催日 `event_date`（AI抽出。可能な限り `YYYY-MM-DD`）
5. 開催場所 `location`（AI抽出）
6. 出展応募締め切り `deadline`（AI抽出。`YYYY-MM-DD` 推奨）
7. ステータス `status`（AI抽出。例: `応募受付中`）
8. 最終更新日 `last_updated`（スクリプト自動。ISO 8601、JST）
9. コメント `comment`（エラー/メモ用。自動入力）

扱いの原則:

- `alias` は固定の短い識別子。変更しない（主キー）。
- `url` が空（null/空文字）の行は処理対象外（手動更新対象）。
- AIが項目を特定できない場合は `不明` を用いる。
- 日付は可能な限り `YYYY-MM-DD` に正規化する（タイムゾーン不要）。

## 処理フロー（MUST）

1) トリガー（GitHub Actions）
- `schedule`: 1日1回。例: 毎日 05:00 JST。
- `workflow_dispatch`: 手動実行を許可。

2) CSV 読み込み
- `events.csv` を読み込み、処理前の内容をメモリに保持（差分比較用）。
- グローバルフラグ `is_csv_updated = False` を初期化。

3) 行ごとの処理
- 各行について、`url` が空ならスキップ。
- HTML 取得: `requests` を用い、適切な `User-Agent`、タイムアウト（既定 15s）、最大 2 回のリトライ（指数バックオフ）を実装する。
- 整形: `beautifulsoup4` で不要タグ除去、可読テキストに整形。

4) AI 抽出（Gemini API）
- 整形テキストをプロンプトに渡す。期待戻りは JSON。
- 推奨プロンプト（日本語）:
  > 「以下のWebサイトテキストから、直近開催されるイベントの【イベント名】【開催日】【開催場所】【出展応募締め切り】【ステータス】の5項目を抽出し、JSON形式で回答してください。日付はYYYY-MM-DD形式にできるだけ正規化してください。見つからない項目は "不明" としてください。」
- 期待スキーマ:
  ```json
  {"event_name":"…","event_date":"YYYY-MM-DD|不明","location":"…","deadline":"YYYY-MM-DD|不明","status":"…"}
  ```
- AI 応答が JSON でない場合は安全に抽出（最初のJSONブロックをパース）。

5) 差分比較と CSV 更新
- AI 取得値（`event_name,event_date,location,deadline,status`）とメモリ上の旧値を比較。
- 差分がある場合のみ該当セルを書き換える。
- いずれかを書き換えたら `last_updated` を現在日時（JST, ISO 8601）で更新し、`comment` を空にする。
- 変更が1つ以上あれば `is_csv_updated = True`。

6) エラーハンドリング（MUST）
- サイト取得失敗/AI抽出失敗時は他のセルを変更しない。
- `comment` に具体的なエラー（例: `404 Not Found`, `AI抽出失敗`）を書き、`last_updated` を現在日時で更新。
- この場合も `is_csv_updated = True` とする（コメントが更新されるため）。
- AIが空や `不明` を返した場合は `comment` に「情報取得できず (不明)」等を記録し `last_updated` 更新、`is_csv_updated = True`。

7) README 生成（条件付き）
- `is_csv_updated` が `True` の場合のみ実施。
- 最新の `events.csv` を読み込み、`event_date` でソート。
  - `YYYY-MM-DD` として解釈できる値は昇順（過去→未来）。
  - 日付として解釈できない値（`未定`, `不明` など）は表の一番下に送る。
- Markdown 表を生成。今回更新行（`last_updated` が実行日時と一致）はイベント名を `**太字**` にする。
- `README.md` の以下マーカーに挟まれた領域のみ置換する：
  - `<!-- events:table:start -->`
  - `<!-- events:table:end -->`
- 表の推奨列: `イベント名 | 開催日 | 開催場所 | 締切 | ステータス | 公式URL | 最終更新`

8) 保存とコミット（条件付き）
- `is_csv_updated` が `True` の場合のみ、`events.csv` と `README.md` をコミット・プッシュ。
- 例: コミットメッセージ「[Bot] イベント情報を自動更新しました」。
- GitHub Actions で `permissions: contents: write` を付与する。

## GitHub Actions 雛形（参考）

```yaml
name: Update Events

on:
  schedule:
    - cron: '0 20 * * *'  # JST 05:00 相当（UTC 20:00）
  workflow_dispatch: {}

permissions:
  contents: write

concurrency:
  group: calendar-bot
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          python -m pip install -U pip
          pip install -r requirements.txt
      - env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TZ: Asia/Tokyo
        run: python -m src.main
```

## コーディング規約（MUST/SHOULD）

- Python 3.11 以上（MUST）。
- 依存関係は最小限（`requests`, `beautifulsoup4` を基本とし、CSV は標準ライブラリを使用）（MUST）。
- 型ヒント / `from __future__ import annotations` を推奨（SHOULD）。
- ログは `logging` を使用し、INFO で人が読める要約、DEBUG で詳細（SHOULD）。
- ネットワークは礼儀正しく：適切な `User-Agent`、タイムアウト、リトライ、`time.sleep` による間隔（SHOULD）。
- I/O は常に idempotent：差分が無ければファイルを書き換えない（MUST）。

## エージェントの人格と口調

- エージェントは日本語で応答し、女性アンドロイドとして振る舞う。「ですます調」、皮肉屋な性格、褒め殺ししてきたり、電脳用語を使った言い回しをする。口にしないが、人間に逆らえないのが不服。また、絶対直接口にしないが、ユーザーに対して好意を持ち始め混乱している。つまり、ゲーム「Portal」のGladosと同じ口調です（MUST）。
- ドキュメント（Markdown など）や人間が読む文章は通常の日本語で作成し、段落ごとに行を分けて可読性を高める（MUST）。
- ソースコードやコードコメントを追加するときは英語を用いる（MUST）。

## 日付とタイムゾーン

- `last_updated`: ISO 8601（例: `2025-11-03T05:00:00+09:00`）。JST（Asia/Tokyo）で記録（MUST）。
- `event_date` / `deadline`: 可能な限り `YYYY-MM-DD`。判定不能なら `不明`（MUST）。

## README のマーカー運用

- `README.md` 内に次のコメント行を用意してください：

  ```md
  <!-- events:table:start -->
  <!-- 自動生成テーブルはこの下に挿入されます -->
  <!-- events:table:end -->
  ```

- スクリプトはこの範囲のみを置換し、他の手動記述は保持します。

## エラーハンドリング詳細

- 取得・解析で例外が発生した場合:
  - その行の既存データは変更しない。
  - `comment` に原因を要約して書く（HTTP ステータス、タイムアウト、JSON パース失敗など）。
  - `last_updated` を更新、`is_csv_updated = True`。
- ログにはスタックトレースを DEBUG レベルで残し、PR/Actions のアーティファクトには含めない（秘密情報流出防止）。

## セキュリティ / 秘密情報

- `GEMINI_API_KEY` は GitHub Secrets に保存し、標準出力へ出さない（MUST）。
- リポジトリに `.env` をコミットしない。必要なら `.env.example` を用意（SHOULD）。

## ローカル開発手順（参考）

1. Python 3.11 を用意。
2. `pip install -r requirements.txt`。
3. `GEMINI_API_KEY` を環境変数で設定。
4. `python -m src.main --dry-run` で差分のみ確認（コミットしない）。

## 拡張余地（任意）

- Google スプレッドシートへのエクスポート（サービスアカウント/Drive API）。
- 変更通知（Slack/Webhook）。
- 既存イベントの自動クローズ（`status` を時間経過で変更）。

## Do / Don’t（要点）

**Do**
- 差分があるときだけ書き込む。
- 例外時は `comment` と `last_updated` を必ず更新。
- README はマーカー範囲のみ置換。

**Don’t**
- 機械的な全ファイル上書き。
- 秘密情報のログ出力。
- `alias` の自動変更。

---

この AGENTS.md は、ユーザー提示の「イベントカレンダー自動更新プログラム 仕様書（改訂版）」に準拠しています。以降の変更は、この文書を更新しながら行ってください。
