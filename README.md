# Neo4j Knowledge Graph with MCP (GitLab Duo / Claude / Cursor)

Docker を利用してローカルに Neo4j ナレッジグラフ環境を構築し、Model Context Protocol (MCP) を通じて GitLab Duo などの AI 支援ツールと連携するためのリポジトリです。
**C言語、Pro*C、COBOL、Pro*COBOL、および Copybook（データ項目）に対応した高機能依存関係・DBアクセス解析スキャナー（`analyzer/scan_repo.py`）** を同梱しています。

---

## 主な機能と解析対象

| 対象言語 / 種別 | 拡張子 | 解析・抽出されるグラフ関係 |
| :--- | :--- | :--- |
| **C / C++** | `.c`, `.h`, `.cpp`, `.hpp` | `#include` (HeaderFile), 関数定義 (`Function`), 関数呼び出し (`CALLS`), マクロ (`Macro`) |
| **Pro*C** | `.pc`, `.pcc` | 埋め込みSQL (`EXEC SQL SELECT / INSERT / UPDATE / DELETE`), 対象DBテーブル (`DatabaseTable`) へのアクセス (`ACCESSES_TABLE`) |
| **COBOL** | `.cbl`, `.cob`, `.cobol` | `PROGRAM-ID`, `COPY`句, 外部プログラム呼出 (`CALL`), 内部制御 (`SECTION` / `PERFORM`) |
| **Pro*COBOL** | `.pco`, `.pbl` | COBOLプログラム内の埋め込みSQL (`EXEC SQL`), DBテーブルアクセス関係 |
| **Copybook** | `.cpy` | コピーブック内部のレコード・フィールド項目 (`CopybookField`), レベル番号, PIC句定義 |

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

### 2. ローカルリポジトリ全体の全精査スキャン
Python 3 標準ライブラリのみで動作します（外部依存パッケージ不要）。

```bash
# 対象リポジトリを指定して直接 Neo4j へ同期する場合
python3 analyzer/scan_repo.py /path/to/your/repository --sync

# Cypher クエリファイル (.cql) として出力する場合
python3 analyzer/scan_repo.py /path/to/your/repository --output-cypher repo_full_graph.cql
```

### 3. GitLab Duo / MCP クライアントの設定
MCP 設定ファイル (`mcp_config.json`) の内容を GitLab Duo や利用する MCP クライアント（Claude Desktop, Cursor 等）に登録します。

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

### 4. GitLab Duo への問い合わせ例
MCP を経由することで、GitLab Duo Chat から高度なレガシー資産分析が可能になります：
- 「`EMP` テーブルを UPDATE している Pro*C や Pro*COBOL のプログラム一覧を教えて」
- 「Copybook `CUSTOMER` を参照しており、その `CUST-BALANCE` 項目を使っているプログラムはどれ？」
- 「プログラム `BATCH02` がアクセスしているデータベーステーブルと実行される SQL 種別（SELECT/INSERT等）を教えて」
- 「`BATCH01` が CALL している全外部プログラムの依存チェーンを図示して」
