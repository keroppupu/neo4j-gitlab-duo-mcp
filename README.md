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
        │ HTTP (7474) : グラフデータ登録 (バッチ同期)
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

## 4. クイックスタートガイド

### ステップ 1: サーバPCで Neo4j コンテナを起動する

サーバとなる PC（またはローカルマシン）で本リポジトリを展開し、コンテナを起動します。

```bash
cd neo4j-gitlab-duo-mcp
docker compose up -d
```

- **Neo4j Web UI**: `http://localhost:7474` （LAN上の別PCからは `http://<サーバIP>:7474`）
- **Bolt 通信ポート**: `7687`
- **初期ユーザー**: `neo4j`
- **初期パスワード**: `password123`

---

### ステップ 2: ローカルリポジトリを全精査して登録する

解析対象のソースコードが存在する PC（LAN上の別PC、またはサーバ自身）からスキャナーを実行します。

#### パターン A: 実行中の Neo4j サーバへ直接同期する（推奨）
```bash
# ローカルで実行する場合
python3 analyzer/scan_repo.py /path/to/target-repo --project "my-project" --sync

# LAN上の別PCからサーバ（例: 192.168.1.100）へ同期する場合
python3 analyzer/scan_repo.py /path/to/target-repo \
    --project "core-banking" \
    --neo4j-url http://192.168.1.100:7474 \
    --user neo4j \
    --password password123 \
    --sync
```

#### パターン B: Cypher クエリファイル (.cql) として出力して確認する場合
```bash
python3 analyzer/scan_repo.py /path/to/target-repo \
    --project "core-banking" \
    --output-cypher graph.cql
```

---

### ステップ 3: GitLab Duo / MCP クライアントを設定する

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

## 5. AI アシスタントへの問い合わせ（プロンプト）例

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

## 6. 保守・セキュリティについて

- **パスワード変更**:
  - 本番運用時は `docker-compose.yml` 内の `NEO4J_AUTH` および各設定ファイルのパスワードを安全な任意の値に変更してください。
- **ファイアウォール設定**:
  - LAN 上の別 PC からアクセスする場合は、サーバ PC のファイアウォールで `7474` (HTTP) および `7687` (Bolt) の受信を許可してください。
- **データ永続化**:
  - 投入されたナレッジグラフのデータはホスト上の `./data` ディレクトリに保存されます。コンテナを再起動・停止してもデータは消失しません。
