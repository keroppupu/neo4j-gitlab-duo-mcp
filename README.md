# Neo4j Knowledge Graph with MCP (GitLab Duo / Claude / Cursor)

Docker を利用してローカルに Neo4j ナレッジグラフ環境を構築し、Model Context Protocol (MCP) を通じて GitLab Duo などの AI 支援ツールと連携するためのリポジトリです。

## 構成
- **Neo4j 5.20** (Docker Compose)
  - APOC プラグイン対応
  - ポート `7474` (ブラウザUI), `7687` (Bolt 通信)
- **MCP サーバー連携設定** (`mcp_config.json`)
  - `@modelcontextprotocol/server-neo4j` を利用して GitLab Duo や各種 MCP クライアントからクエリ・スキーマ参照が可能

## 起動方法

### 1. Neo4j コンテナの起動
```bash
docker compose up -d
```

起動後、ブラウザで [http://localhost:7474](http://localhost:7474) にアクセスできます。
- **Connect URL**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: `password123`

### 2. GitLab Duo / MCP クライアントの設定
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

## サンプルクエリ (Cypher)
ブラウザまたは MCP 経由でグラフデータを投入・確認できます：

```cypher
// プロジェクトと技術要素の関連付けサンプル
CREATE (p:Project {name: 'MyMicroservice'})
CREATE (s:Service {name: 'AuthService'})
CREATE (d:Database {name: 'Neo4j'})
CREATE (p)-[:CONTAINS]->(s)
CREATE (s)-[:CONNECTS_TO]->(d)
RETURN p, s, d;
```
