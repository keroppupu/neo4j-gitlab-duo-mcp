#!/usr/bin/env python3
"""
Enterprise Multi-Project C / COBOL / Pro*C / Pro*COBOL Dependency & Database Graph Analyzer for Neo4j.

Supports:
- Multi-project isolation & cross-project relationships via (:Project) nodes and project property tagging.
- C / C++ (.c, .h, .cpp, .hpp)
- Pro*C (.pc, .pcc) - Embedded SQL
- COBOL (.cbl, .cob, .cobol)
- Pro*COBOL (.pco, .pbl) - Embedded SQL in COBOL
- Copybook (.cpy) - Data Division structure & fields parser
- LAN server sync via --neo4j-url http://<SERVER_IP>:7474 --sync
"""

import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path


class SqlExtractor:
    EXEC_SQL_C_REGEX = re.compile(r'EXEC\s+SQL\s+(.*?);', re.IGNORECASE | re.DOTALL)
    EXEC_SQL_COBOL_REGEX = re.compile(r'EXEC\s+SQL\s+(.*?)END-EXEC', re.IGNORECASE | re.DOTALL)

    TABLE_FROM_REGEX = re.compile(r'\b(?:FROM|JOIN|UPDATE|INTO)\s+([a-zA-Z0-9_\$#]+)', re.IGNORECASE)
    SQL_ACTION_REGEX = re.compile(r'^\s*(SELECT|INSERT|UPDATE|DELETE|INCLUDE|DECLARE|OPEN|FETCH|CLOSE|COMMIT|ROLLBACK)\b', re.IGNORECASE)

    KEYWORDS = {'SET', 'VALUES', 'WHERE', 'AND', 'OR', 'SELECT', 'FROM', 'INTO', 'TABLE', 'INDEX', 'VIEW', 'BEGIN', 'END', 'SECTION', 'SQLCA'}

    @classmethod
    def extract_sql_from_c(cls, content: str):
        operations = []
        for match in cls.EXEC_SQL_C_REGEX.finditer(content):
            sql_text = " ".join(match.group(1).split())
            action_match = cls.SQL_ACTION_REGEX.search(sql_text)
            action = action_match.group(1).upper() if action_match else "SQL"
            
            tables = set()
            for t_match in cls.TABLE_FROM_REGEX.finditer(sql_text):
                tbl = t_match.group(1).upper()
                if tbl not in cls.KEYWORDS:
                    tables.add(tbl)

            operations.append({
                "action": action,
                "tables": list(tables),
                "raw_sql": sql_text[:120]
            })
        return operations

    @classmethod
    def extract_sql_from_cobol(cls, content: str):
        operations = []
        for match in cls.EXEC_SQL_COBOL_REGEX.finditer(content):
            sql_text = " ".join(match.group(1).split())
            action_match = cls.SQL_ACTION_REGEX.search(sql_text)
            action = action_match.group(1).upper() if action_match else "SQL"

            tables = set()
            for t_match in cls.TABLE_FROM_REGEX.finditer(sql_text):
                tbl = t_match.group(1).upper()
                if tbl not in cls.KEYWORDS:
                    tables.add(tbl)

            operations.append({
                "action": action,
                "tables": list(tables),
                "raw_sql": sql_text[:120]
            })
        return operations


class CAndProCParser:
    INCLUDE_REGEX = re.compile(r'^[ \t]*#include\s*([<"])([^>"]+)([>"])', re.MULTILINE)
    MACRO_REGEX = re.compile(r'^[ \t]*#define\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    FUNC_DEF_REGEX = re.compile(
        r'^[ \t]*(?:static\s+|inline\s+|extern\s+)?(?:const\s+)?(?:[a-zA-Z_][a-zA-Z0-9_* \t]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^;]*?)\)\s*\{',
        re.MULTILINE | re.DOTALL
    )
    FUNC_CALL_REGEX = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')

    def parse(self, file_path: str, rel_path: str, content: str, is_proc: bool = False):
        file_name = os.path.basename(file_path)
        data = {
            "type": "Pro*C" if is_proc else "C",
            "file": file_name,
            "path": rel_path,
            "includes": [],
            "macros": [],
            "functions": [],
            "calls": [],
            "sql_operations": []
        }

        for m in self.INCLUDE_REGEX.finditer(content):
            data["includes"].append({
                "target": m.group(2),
                "is_system": m.group(1) == '<'
            })

        for m in self.MACRO_REGEX.finditer(content):
            data["macros"].append(m.group(1))

        matches = list(self.FUNC_DEF_REGEX.finditer(content))
        for i, match in enumerate(matches):
            func_name = match.group(1)
            if func_name in {'if', 'for', 'while', 'switch'}:
                continue
            data["functions"].append(func_name)

            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start_pos:end_pos]

            for call in set(self.FUNC_CALL_REGEX.findall(body)):
                if call not in {'if', 'for', 'while', 'switch'} and call != func_name:
                    data["calls"].append({"caller": func_name, "callee": call})

        if is_proc or "EXEC SQL" in content.upper():
            data["sql_operations"] = SqlExtractor.extract_sql_from_c(content)

        return data


class CopybookParser:
    FIELD_REGEX = re.compile(r'^[ \t]*(\d{2})\s+([a-zA-Z0-9_\-]+)(?:\s+PIC\s+([a-zA-Z0-9()vVsS]+))?', re.MULTILINE | re.IGNORECASE)

    def parse(self, file_path: str, rel_path: str, content: str):
        file_name = os.path.basename(file_path)
        cb_name = os.path.splitext(file_name)[0].upper()
        
        data = {
            "type": "COPYBOOK",
            "file": file_name,
            "path": rel_path,
            "copybook_name": cb_name,
            "fields": []
        }

        for line in content.splitlines():
            if re.match(r'^\d{6}', line):
                line = line[6:]
            if line.startswith('*') or line.startswith('/'):
                continue
            
            m = self.FIELD_REGEX.search(line)
            if m:
                level = m.group(1)
                name = m.group(2).upper()
                pic = m.group(3) or ""
                if name not in {'FILLER', 'END-EXEC'}:
                    data["fields"].append({
                        "level": level,
                        "name": name,
                        "pic": pic
                    })

        return data


class CobolAndProCobolParser:
    PROGRAM_ID_REGEX = re.compile(r'PROGRAM-ID\.\s*([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    COPY_REGEX = re.compile(r'\bCOPY\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    CALL_REGEX = re.compile(r'\bCALL\s+["\']([a-zA-Z0-9_\-]+)["\']', re.IGNORECASE)
    PERFORM_REGEX = re.compile(r'\bPERFORM\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    SECTION_REGEX = re.compile(r'^[ \t]*([a-zA-Z0-9_\-]+)\s*(?:SECTION|PROCEDURE)?\.\s*$', re.MULTILINE | re.IGNORECASE)
    RESERVED = {'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE', 'DIVISION', 'WORKING-STORAGE', 'STOP', 'RUN'}

    def parse(self, file_path: str, rel_path: str, content: str, is_procobol: bool = False):
        file_name = os.path.basename(file_path)
        prog_match = self.PROGRAM_ID_REGEX.search(content)
        program_id = prog_match.group(1).upper() if prog_match else file_name.rsplit('.', 1)[0].upper()

        data = {
            "type": "Pro*COBOL" if is_procobol else "COBOL",
            "file": file_name,
            "path": rel_path,
            "program_id": program_id,
            "copybooks": [],
            "calls": [],
            "sections": [],
            "performs": [],
            "sql_operations": []
        }

        cleaned_lines = []
        for line in content.splitlines():
            if re.match(r'^\d{6}', line):
                line = line[6:]
            if line.startswith('*') or line.startswith('/'):
                continue
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines)

        data["copybooks"] = list(set(self.COPY_REGEX.findall(cleaned)))
        data["calls"] = list(set(self.CALL_REGEX.findall(cleaned)))

        for m in self.SECTION_REGEX.finditer(cleaned):
            sec = m.group(1).strip().upper()
            if sec not in self.RESERVED and not sec.endswith('-SECTION') and sec not in data["sections"]:
                data["sections"].append(sec)

        for m in self.PERFORM_REGEX.finditer(cleaned):
            tgt = m.group(1).strip().upper()
            if tgt not in self.RESERVED and tgt not in data["performs"]:
                data["performs"].append(tgt)

        if is_procobol or "EXEC SQL" in content.upper():
            data["sql_operations"] = SqlExtractor.extract_sql_from_cobol(content)

        return data


def scan_repository(repo_root):
    c_parser = CAndProCParser()
    cobol_parser = CobolAndProCobolParser()
    copybook_parser = CopybookParser()
    results = []

    c_exts = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx'}
    proc_exts = {'.pc', '.pcc'}
    cobol_exts = {'.cbl', '.cob', '.cobol'}
    procobol_exts = {'.pco', '.pbl'}
    copybook_exts = {'.cpy'}

    ignore_dirs = {'.git', 'node_modules', 'dist', 'build', 'out', 'venv', '.venv'}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, repo_root)
            ext = os.path.splitext(f)[1].lower()

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
            except Exception as e:
                print(f"[-] Could not read {rel_path}: {e}")
                continue

            if ext in proc_exts or (ext in c_exts and "EXEC SQL" in content.upper()):
                results.append(c_parser.parse(path, rel_path, content, is_proc=True))
            elif ext in c_exts:
                results.append(c_parser.parse(path, rel_path, content, is_proc=False))
            elif ext in copybook_exts:
                results.append(copybook_parser.parse(path, rel_path, content))
            elif ext in procobol_exts or (ext in cobol_exts and "EXEC SQL" in content.upper()):
                results.append(cobol_parser.parse(path, rel_path, content, is_procobol=True))
            elif ext in cobol_exts:
                results.append(cobol_parser.parse(path, rel_path, content, is_procobol=False))

    return results


def build_graph_statements(results, project_name="default"):
    """
    Builds graph statements with multi-project scoping.
    Every artifact connects to a (:Project {name: $project_name}) node and has project property.
    Database tables can be shared across projects to detect cross-project data dependencies.
    """
    statements = []

    # Project Node
    statements.append(f"""
    MERGE (proj:Project {{name: '{project_name}'}})
    """)

    for item in results:
        f_name = item["file"]
        f_path = item["path"]
        f_type = item["type"]

        # Base File Node linked to Project
        statements.append(f"""
        MERGE (proj:Project {{name: '{project_name}'}})
        MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
        SET f.name = '{f_name}', f.type = '{f_type}'
        MERGE (proj)-[:CONTAINS_FILE]->(f)
        """)

        # 1. Copybook
        if f_type == "COPYBOOK":
            cb_name = item["copybook_name"]
            statements.append(f"""
            MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
            MERGE (cb:Copybook {{name: '{cb_name}', project: '{project_name}'}})
            SET cb.file = '{f_path}'
            MERGE (f)-[:CONTAINS]->(cb)
            """)

            for field in item["fields"]:
                f_level = field["level"]
                fld_name = field["name"]
                f_pic = field["pic"]
                statements.append(f"""
                MERGE (cb:Copybook {{name: '{cb_name}', project: '{project_name}'}})
                MERGE (cf:CopybookField {{name: '{fld_name}', copybook: '{cb_name}', project: '{project_name}'}})
                SET cf.level = '{f_level}', cf.pic = '{f_pic}'
                MERGE (cb)-[:DEFINES_FIELD]->(cf)
                """)

        # 2. C / Pro*C
        elif f_type in ("C", "Pro*C"):
            for inc in item["includes"]:
                statements.append(f"""
                MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
                MERGE (inc:HeaderFile {{name: '{inc["target"]}', project: '{project_name}'}})
                SET inc.is_system = {str(inc["is_system"]).lower()}
                MERGE (f)-[:INCLUDES]->(inc)
                """)

            for fn in item["functions"]:
                statements.append(f"""
                MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
                MERGE (fn:Function {{name: '{fn}', project: '{project_name}', file: '{f_path}'}})
                MERGE (f)-[:DEFINES]->(fn)
                """)

            for call in item["calls"]:
                statements.append(f"""
                MERGE (caller:Function {{name: '{call["caller"]}', project: '{project_name}', file: '{f_path}'}})
                MERGE (callee:Function {{name: '{call["callee"]}', project: '{project_name}'}})
                MERGE (caller)-[:CALLS]->(callee)
                """)

            # Database Table access (DatabaseTable node is globally identified by name across projects)
            for sql in item.get("sql_operations", []):
                action = sql["action"]
                for tbl in sql["tables"]:
                    statements.append(f"""
                    MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
                    MERGE (t:DatabaseTable {{name: '{tbl}'}})
                    MERGE (f)-[:ACCESSES_TABLE {{action: '{action}', project: '{project_name}'}}]->(t)
                    """)

        # 3. COBOL / Pro*COBOL
        elif f_type in ("COBOL", "Pro*COBOL"):
            prog = item["program_id"]
            statements.append(f"""
            MERGE (f:SourceFile {{path: '{f_path}', project: '{project_name}'}})
            MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
            SET p.file = '{f_path}', p.is_procobol = {str(f_type == "Pro*COBOL").lower()}
            MERGE (f)-[:CONTAINS]->(p)
            """)

            for cpy in item["copybooks"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
                MERGE (cb:Copybook {{name: '{cpy.upper()}', project: '{project_name}'}})
                MERGE (p)-[:COPIES]->(cb)
                """)

            for ext_call in item["calls"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
                MERGE (sub:CobolProgram {{name: '{ext_call.upper()}', project: '{project_name}'}})
                MERGE (p)-[:CALLS]->(sub)
                """)

            for sec in item["sections"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
                MERGE (s:Section {{name: '{sec}', program: '{prog}', project: '{project_name}'}})
                MERGE (p)-[:DEFINES_SECTION]->(s)
                """)

            for perf in item["performs"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
                MERGE (s:Section {{name: '{perf}', program: '{prog}', project: '{project_name}'}})
                MERGE (p)-[:PERFORMS]->(s)
                """)

            for sql in item.get("sql_operations", []):
                action = sql["action"]
                for tbl in sql["tables"]:
                    statements.append(f"""
                    MERGE (p:CobolProgram {{name: '{prog}', project: '{project_name}'}})
                    MERGE (t:DatabaseTable {{name: '{tbl}'}})
                    MERGE (p)-[:ACCESSES_TABLE {{action: '{action}', project: '{project_name}'}}]->(t)
                    """)

    return statements


def execute_cypher_via_http(statements, neo4j_url="http://localhost:7474", auth=("neo4j", "password123")):
    endpoint = f"{neo4j_url.rstrip('/')}/db/neo4j/tx/commit"
    tx_statements = [{"statement": stmt.strip()} for stmt in statements if stmt.strip()]
    if not tx_statements:
        print("[!] No statements to execute.")
        return True

    payload = json.dumps({"statements": tx_statements}).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
    
    import base64
    auth_str = f"{auth[0]}:{auth[1]}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {b64_auth}")

    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            errors = resp_data.get("errors", [])
            if errors:
                print(f"[!] Neo4j Error: {errors}")
                return False
            print(f"[+] Successfully executed {len(tx_statements)} graph statements in Neo4j.")
            return True
    except urllib.error.URLError as e:
        print(f"[-] Could not connect to Neo4j HTTP API at {endpoint}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Multi-Project Enterprise C/COBOL/Pro*C/Pro*COBOL/Copybook Analyzer")
    parser.add_argument("repo_path", nargs="?", default=".", help="Root path of repository to inspect (default: current directory)")
    parser.add_argument("--project", help="Project name (defaults to repository folder name)")
    parser.add_argument("--output-cypher", help="File to write Cypher statements (.cql)")
    parser.add_argument("--neo4j-url", default="http://localhost:7474", help="Neo4j HTTP base URL (default: http://localhost:7474)")
    parser.add_argument("--user", default="neo4j", help="Neo4j user")
    parser.add_argument("--password", default="password123", help="Neo4j password")
    parser.add_argument("--sync", action="store_true", help="Sync directly to running Neo4j container")

    args = parser.parse_args()
    repo_root = os.path.abspath(args.repo_path)
    project_name = args.project or os.path.basename(repo_root)

    print(f"============================================================")
    print(f"[*] Enterprise Multi-Project Scanner")
    print(f"[*] Target Directory: {repo_root}")
    print(f"[*] Project Name    : {project_name}")
    print(f"============================================================")

    results = scan_repository(repo_root)
    types_count = {}
    for r in results:
        t = r["type"]
        types_count[t] = types_count.get(t, 0) + 1

    print(f"[+] Found {len(results)} source artifacts:")
    for t, cnt in types_count.items():
        print(f"    - {t}: {cnt}")

    statements = build_graph_statements(results, project_name=project_name)
    print(f"[+] Generated {len(statements)} graph relationship statements (scoped to project '{project_name}').")

    if args.output_cypher:
        with open(args.output_cypher, "w", encoding="utf-8") as fp:
            for s in statements:
                fp.write(s.strip() + ";\n\n")
        print(f"[+] Saved Cypher queries to: {args.output_cypher}")

    if args.sync:
        print(f"[*] Syncing to Neo4j ({args.neo4j_url})...")
        execute_cypher_via_http(statements, neo4j_url=args.neo4j_url, auth=(args.user, args.password))

    print(f"[+] Multi-project inspection completed.")


if __name__ == "__main__":
    main()
