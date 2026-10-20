# Neo4j Knowledge Graph with MCP (GitLab Duo / Claude / Cursor)

Docker を利用してローカルに Neo4j ナレッジグラフ環境を構築し、Model Context Protocol (MCP) を通じて GitLab Duo などの AI 支援ツールと連携するためのリポジトリです。
**C言語およびCOBOLソースコードの自動依存関係解析ツール（`analyzer/`）** を同梱しています。

## 構成
- **Neo4j 5.20** (Docker Compose)
  - APOC プラグイン対応
  - ポート `7474` (ブラウザUI), `7687` (Bolt 通信)
- **C & COBOL 独自依存関係解析ツール** (`analyzer/analyze_dependencies.py`)
  - **C言語**: `#include` (HeaderFile), 関数定義 (`Function`), 関数呼び出し (`CALLS`)
  - **COBOL**: `PROGRAM-ID`, `COPY` (Copybook), `CALL` (外部プログラム呼出), `SECTION` / `PERFORM` (内部制御フロー)
  - Neo4j HTTP API 経由での自動直接投入 (`--sync`) および `.cql` 出力に対応
- **GitLab CI/CD 自動連携テンプレート** (`.gitlab-ci.yml`)
  - リポジトリへのプッシュ時に C/COBOL を自動解析して Neo4j へ同期
- **MCP サーバー連携設定** (`mcp_config.json`)
  - `@modelcontextprotocol/server-neo4j` を利用して GitLab Duo や各種 MCP クライアントからクエリ・スキーマ参照が可能

---

## 起動・使用方法

### 1. Neo4j コンテナの起動
```bash
docker compose up -d
```
ブラウザで [http://localhost:7474](http://localhost:7474) にアクセスできます。
- **Connect URL**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: `password123`

### 2. C / COBOL ソースコードの自動解析 & Neo4j への投入
Python 3 標準ライブラリのみで動作します（外部依存パッケージ不要）。

```bash
# 解析と同時に実行中の Neo4j へ登録する場合
python3 analyzer/analyze_dependencies.py /path/to/source_dir --sync

# Cypherクエリファイル (.cql) として出力する場合
python3 analyzer/analyze_dependencies.py /path/to/source_dir --output-cypher graph.cql
```

### 3. GitLab Duo / MCP クライアントの設定
MCP 設定ファイル (`mcp_config.json`) の内容を GitLab Duo や利用する MCP クライアントの設定ファイル（例: `claude_desktop_config.json` 等）に登録します。

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-neo4j"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password123"
      }
    }
  }
}
```

### 4. GitLab Duo へのプロンプト例
MCP 連携後、GitLab Duo Chat などで以下のように質問できます：
- 「`BATCH01` が呼び出している外部プログラムやサブセクションの一覧を教えて」
- 「`process_data` 関数が依存しているヘッダーや呼び出し先関数を図示して」
- 「`db_utils.h` をインクルードしているソースファイル一覧を検索して」
