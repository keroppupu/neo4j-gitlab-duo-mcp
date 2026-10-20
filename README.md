# Enterprise Neo4j Knowledge Graph with MCP (GitLab Duo / Claude / Cursor)

Docker を利用してローカルまたは LAN サーバ上に **Neo4j ナレッジグラフ環境** を立ち上げ、**C / Pro\*C / COBOL / Pro\*COBOL / Copybook** の資産を全精査・グラフデータベース化して、**Model Context Protocol (MCP)** を介して **GitLab Duo** や **Claude Desktop**、**Cursor** などの AI アシスタントと連携させるための統合ソリューションリポジトリです。

---

## 1. 全体像とアーキテクチャ

本システムは、チーム内の複数プロジェクトやレガシー言語（C/COBOL系）資産の依存関係・DBアクセス構造をナレッジグラフ化し、AI から自然言語で高精度に照会できるように設計されています。

```text
[ 開発者クライアントPC (LAN上の各PC) ]
  ├── ローカルリポジトリ (C / Pro*C / COBOL / Pro*COBOL / Copybook)
  │     git pull してきたソースコード
  │
  ├── 独自全精査スキャナー (analyzer/scan_repo.py)
  │     └─ 構文解析・依存関係・SQL・Copybookフィールド抽出
  │
  └── GitLab Duo / Claude / Cursor (MCP Client)
        │
        │ HTTP (7474) : グラフデータ登録 (バッチ分割同期)
        │ Bolt (7687) : MCP経由での自然言語クエリ参照
        ▼
[ サーバPC (LAN上の常時稼働ホスト) ]
  └── Docker コンテナ (Neo4j ナレッジグラフ)
        ├── Multi-Project スコープ管理 (:Project)
        ├── 共通 DB テーブル連携 (:DatabaseTable)
        └── 永続化ストレージ (./data)
```

---

## 2. 主な特徴

- **マルチ言語・レガシー言語対応**:
  - **C / C++**: `#include`（ローカル/システムヘッダー判定）、マクロ定義（`#define`）、関数定義、関数呼び出し関係（`CALLS`）。
  - **Pro\*C**: 埋め込み SQL（`EXEC SQL SELECT / INSERT / UPDATE / DELETE`）および対象テーブルへのアクセス関係（`ACCESSES_TABLE`）。
  - **COBOL**: `PROGRAM-ID`、`COPY`句、外部サブプログラム呼出（`CALL`）、内部制御（`SECTION` / `PERFORM`）。
  - **Pro\*COBOL**: COBOL内の埋め込み SQL、DBテーブルアクセス関係。
  - **Copybook (`.cpy`)**: コピーブック内の階層レベル番号（`01`, `05` 等）、フィールド名、`PIC` 句（`PIC X(10)`, `PIC S9(9)V99` 等）の項目構造を網羅解析。
- **マルチプロジェクト対応**:
  - 1つの Neo4j サーバ内で複数の独立したプロジェクト/リポジトリをタグ付け（`project: "名前"`）して同名衝突なしに同時管理。
  - 複数プロジェクト間で参照されている共通の DB テーブルを横断結合し、システム間連携の影響調査が可能。
- **LAN サーバ運用 & クライアントスキャン**:
  - サーバ側は Docker コンテナとして常時起動。
  - クライアント PC 側は Python 3 標準ライブラリのみで動作（追加パッケージ導入不要）。LAN 経由でサーバへ一括登録。
- **AI (GitLab Duo / Claude / Cursor) との MCP 連携**:
  - `@modelcontextprotocol/server-neo4j` を介して、自然言語でグラフ構造や影響範囲を即座に回答。

---

## 3. ディレクトリ構成

```text
.
├── docker-compose.yml          # Neo4j グラフDBコンテナ構成定義
├── mcp_config.json             # GitLab Duo / MCPクライアント向け接続設定
├── .gitlab-ci.yml              # GitLab CI/CD 用自動スキャン&同期パイプライン
├── README.md                   # 全体説明・利用マニュアル
└── analyzer/
    ├── scan_repo.py            # 全精査スキャナー本体 (マルチ言語・マルチプロジェクト・LAN同期)
    └── sample_code/            # 動作検証用サンプルコード (C, Pro*C, COBOL, Pro*COBOL, Copybook)
        ├── main.c
        ├── db_utils.h / db_utils.c
        ├── db_ops.pc
        ├── BATCH01.cbl
        ├── BATCH02.pco
        ├── SUBPROG1.cbl
        └── CUSTOMER.cpy
```

---

## 4. ローカルスキャンの詳細手順ガイド（重要）

`analyzer/scan_repo.py` は、クライアント PC 上に `git pull` してきたローカルリポジトリを再帰的に走査し、構文・依存関係を解析して Neo4j サーバへ登録するためのツールです。

### 4.1 前提環境・動作要件
- **クライアント PC**: Python 3.7 以上がインストールされていること。
  - **外部ライブラリのインストール（pip）は一切不要です**（Python 標準ライブラリ `urllib`, `re`, `json`, `argparse` のみで動作します）。
  - クライアント PC 側に Docker や Neo4j は不要です。
- **ネットワーク接続**: クライアント PC から Neo4j サーバの IP（例: `http://192.168.1.100:7474`）へ HTTP 通信ができること。

---

### 4.2 コマンドライン引数リファレンス

```bash
python3 analyzer/scan_repo.py [対象ディレクトリパス] [オプション...]
```

| 引数・オプション | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `repo_path` | `.` (カレントディレクトリ) | スキャン対象のローカルリポジトリまたはソースコードのルートパス。 |
| `--project` | ディレクトリ名 | プロジェクト識別名。Neo4j 内で `(:Project {name: "..."})` として紐づけられます。 |
| `--neo4j-url` | `http://localhost:7474` | 接続先 Neo4j サーバの HTTP URL。LAN 上のサーバの場合は `http://<サーバIP>:7474` を指定。 |
| `--user` | `neo4j` | Neo4j の認証ユーザー名。 |
| `--password` | `password123` | Neo4j の認証パスワード。 |
| `--sync` | なし（フラグ） | **指定すると、解析結果を即座に Neo4j サーバへバッチコミット登録します。** |
| `--output-cypher` | なし | 生成された Cypher クエリ文をファイル（`.cql`）としてローカル保存する場合にファイルパスを指定。 |

---

### 4.3 スキャン実行シナリオ別コマンド例

#### シナリオ 1: 開発PCから LAN 上の Neo4j サーバへ直接同期する（標準的な運用）
クライアント PC に `git pull` してきたリポジトリを、プロジェクト名を明示してサーバへ一括登録します。

```bash
python3 analyzer/scan_repo.py /Users/developer/projects/core-banking \
    --project "core-banking" \
    --neo4j-url http://192.168.1.100:7474 \
    --user neo4j \
    --password password123 \
    --sync
```
**実行出力例:**
```text
============================================================
[*] Enterprise Multi-Project Scanner
[*] Target Directory: /Users/developer/projects/core-banking
[*] Project Name    : core-banking
============================================================
[+] Found 142 source artifacts:
    - COBOL: 90
    - COPYBOOK: 35
    - Pro*COBOL: 17
[+] Generated 1,280 graph relationship statements (scoped to project 'core-banking').
[*] Syncing to Neo4j (http://192.168.1.100:7474)...
[*] Progress: 50/1280 statements committed.
[*] Progress: 100/1280 statements committed.
...
[+] Successfully executed all 1280 graph statements in Neo4j.
[+] Multi-project inspection completed.
```

#### シナリオ 2: サーバに登録する前に生成クエリを確認・保存したい場合
`--sync` を付けずに `--output-cypher` を指定することで、ローカルに `.cql` ファイルを出力して中身を確認できます。

```bash
python3 analyzer/scan_repo.py /path/to/my-repo \
    --project "billing-system" \
    --output-cypher billing_graph.cql
```

#### シナリオ 3: 同一マシン上で Docker とスキャナーを動かす場合
`--neo4j-url` の指定を省略（デフォルト `localhost:7474`）して実行できます。

```bash
python3 analyzer/scan_repo.py ./analyzer/sample_code --project "demo" --sync
```

---

### 4.4 スキャン処理の詳細な仕組み・挙動
1. **ディレクトリの自動探索と除外処理**:
   - 指定されたディレクトリ配下を再帰的に走査します。
   - `.git`, `node_modules`, `dist`, `build`, `out`, `venv`, `.venv` などの管理・ビルド生成ディレクトリは**自動でスキップ**され、不要なファイルを読み込みません。
2. **言語別の厳密なパース処理**:
   - **C / Pro\*C**: コメント行（`/* ... */`, `// ...`）を安全に除去し、文字列内のクォートやエスケープ文字を正しく扱って誤検知を防ぎます。
   - **COBOL / Pro\*COBOL**: 6桁の行番号や7カラム目のコメントマーク（`*`, `/`）を自動トリミングしてプログラムID、CALL文、PERFORM文を抽出します。
   - **Copybook (`.cpy`)**: フィールドのレベル番号（01, 05等）および `PIC` 句をすべて抽出し、階層関係を保持します。
   - **SQL 文抽出**: `EXEC SQL ... ;` または `EXEC SQL ... END-EXEC` をキャッチし、テーブル名と操作種別（SELECT, INSERT, UPDATE, DELETE等）を特定します。
3. **バッチ分割コミットによる安定同期**:
   - 抽出された数千〜数万件のノード・エッジ登録ステートメントは、50件ごとのチャンクに分割されて Neo4j のトランザクション API（HTTP POST）へ送信されます。
   - これにより、大規模リポジトリを登録する際でもネットワークタイムアウトやサーバ側のメモリ枯渇を起こさずに安全に同期されます。

---

## 5. GitLab Duo / MCP クライアントの設定手順

GitLab Duo や Claude Desktop、Cursor などの設定ファイル（例: `claude_desktop_config.json` 等）に、以下の MCP サーバー設定を登録します。

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-neo4j"
      ],
      "env": {
        "NEO4J_URI": "bolt://<サーバのIPアドレスまたはlocalhost>:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password123"
      }
    }
  }
}
```

---

## 6. AI アシスタントへの問い合わせ（プロンプト）例

MCP 接続後、GitLab Duo やチャット画面から以下のような質問を行うことで、ナレッジグラフを活用した高精度な回答が得られます：

1. **データベース影響調査**:
   > 「テーブル `ACCOUNTS` を更新（UPDATE/INSERT）している全プロジェクトの Pro\*COBOL および Pro\*C のプログラムを教えて」
2. **Copybook・データ構造の影響調査**:
   > 「Copybook `CUSTOMER` のフィールド `CUST-BALANCE` を参照している COBOL プログラムと、その呼び出し元の依存関係を図示して」
3. **プログラム呼出チェーンの追跡**:
   > 「`BATCH01` プログラムから CALL されている外部サブプログラムと、PERFORM されている内部セクションをツリー形式で出力して」
4. **プロジェクト間共通資産の分析**:
   > 「`core-banking` と `billing-system` の両方のプロジェクトから共有・参照されているデータベーステーブルの一覧を出して」

---

## 7. 保守・セキュリティについて

- **パスワード変更**:
  - 本番運用時は `docker-compose.yml` 内の `NEO4J_AUTH` および各設定ファイルのパスワードを安全な任意の値に変更してください。
- **ファイアウォール設定**:
  - LAN 上の別 PC からアクセスする場合は、サーバ PC のファイアウォールで `7474` (HTTP) および `7687` (Bolt) の受信を許可してください。
- **データ永続化**:
  - 投入されたナレッジグラフのデータはホスト上の `./data` ディレクトリに保存されます。コンテナを再起動・停止してもデータは消失しません。
