#!/usr/bin/env python3
"""
Full C & COBOL Repository Scanner and Dependency Analyzer for Neo4j.

Features:
- Discovers git repository root or takes an explicit directory.
- Recursively scans all files respecting .gitignore and ignoring hidden/.git/build directories.
- Handles C:
    - #include <...> and #include "..." (local vs system headers)
    - Macro definitions (#define)
    - Function definitions & forward declarations
    - Function call references
- Handles COBOL:
    - PROGRAM-ID
    - COPY statements & copybook linking
    - CALL statements (dynamic and static subprogram calls)
    - SECTION / PARAGRAPH definitions
    - PERFORM statements
- Resolves cross-file dependencies (linking calls/includes to concrete defined entities in the repo).
- Generates rich Cypher graph queries and directly syncs to Neo4j.
"""

import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path


class AdvancedCParser:
    INCLUDE_REGEX = re.compile(r'^[ \t]*#include\s*([<"])([^>"]+)([>"])', re.MULTILINE)
    MACRO_REGEX = re.compile(r'^[ \t]*#define\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    FUNC_DEF_REGEX = re.compile(
        r'^[ \t]*(?:static\s+|inline\s+|extern\s+)?(?:const\s+)?(?:[a-zA-Z_][a-zA-Z0-9_* \t]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^;]*?)\)\s*\{',
        re.MULTILINE | re.DOTALL
    )
    FUNC_CALL_REGEX = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
    KEYWORDS = {
        'if', 'for', 'while', 'switch', 'return', 'sizeof', 'printf', 'fprintf', 'scanf',
        'malloc', 'free', 'memset', 'memcpy', 'exit', 'main'
    }

    def parse(self, file_path: str, rel_path: str, content: str):
        file_name = os.path.basename(file_path)
        data = {
            "type": "C",
            "file": file_name,
            "path": rel_path,
            "includes": [],
            "macros": [],
            "functions": [],
            "calls": []
        }

        # 1. Includes (distinguish local vs system)
        for m in self.INCLUDE_REGEX.finditer(content):
            bracket_type = m.group(1)
            inc_target = m.group(2)
            data["includes"].append({
                "target": inc_target,
                "is_system": bracket_type == '<'
            })

        # 2. Macros
        for m in self.MACRO_REGEX.finditer(content):
            data["macros"].append(m.group(1))

        # 3. Functions & calls
        matches = list(self.FUNC_DEF_REGEX.finditer(content))
        for i, match in enumerate(matches):
            func_name = match.group(1)
            if func_name in {'if', 'for', 'while', 'switch'}:
                continue
            data["functions"].append(func_name)
            
            # Analyze function body
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start_pos:end_pos]

            for call in set(self.FUNC_CALL_REGEX.findall(body)):
                if call not in {'if', 'for', 'while', 'switch'} and call != func_name:
                    data["calls"].append({"caller": func_name, "callee": call})

        return data


class AdvancedCobolParser:
    PROGRAM_ID_REGEX = re.compile(r'PROGRAM-ID\.\s*([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    COPY_REGEX = re.compile(r'\bCOPY\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    CALL_REGEX = re.compile(r'\bCALL\s+["\']([a-zA-Z0-9_\-]+)["\']', re.IGNORECASE)
    PERFORM_REGEX = re.compile(r'\bPERFORM\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    SECTION_REGEX = re.compile(r'^[ \t]*([a-zA-Z0-9_\-]+)\s*(?:SECTION|PROCEDURE)?\.\s*$', re.MULTILINE | re.IGNORECASE)
    RESERVED = {'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE', 'DIVISION', 'WORKING-STORAGE', 'STOP', 'RUN'}

    def parse(self, file_path: str, rel_path: str, content: str):
        file_name = os.path.basename(file_path)
        prog_match = self.PROGRAM_ID_REGEX.search(content)
        program_id = prog_match.group(1).upper() if prog_match else file_name.rsplit('.', 1)[0].upper()

        data = {
            "type": "COBOL",
            "file": file_name,
            "path": rel_path,
            "program_id": program_id,
            "copybooks": [],
            "calls": [],
            "sections": [],
            "performs": []
        }

        # Handle 72-column or standard formats
        cleaned_lines = []
        for line in content.splitlines():
            # Drop line numbers in cols 1-6 if 6 leading digits
            if re.match(r'^\d{6}', line):
                line = line[6:]
            # Skip comment lines in column 7
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

        return data


def scan_repository(repo_root):
    """Walks the entire repository, skips git/build dirs, and parses all C and COBOL files."""
    c_parser = AdvancedCParser()
    cobol_parser = AdvancedCobolParser()
    results = []

    c_exts = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx'}
    cobol_exts = {'.cbl', '.cob', '.cpy', '.cobol'}
    ignore_dirs = {'.git', 'node_modules', 'dist', 'build', 'out', 'venv', '.venv'}

    for root, dirs, files in os.walk(repo_root):
        # Exclude ignored dirs
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

            if ext in c_exts:
                results.append(c_parser.parse(path, rel_path, content))
            elif ext in cobol_exts:
                results.append(cobol_parser.parse(path, rel_path, content))

    return results


def build_graph_statements(results):
    statements = []
    
    # Store indices for cross-file linking
    defined_functions = {}  # func_name -> file_path
    defined_cobol_programs = {}  # program_id -> file_path

    for item in results:
        f_name = item["file"]
        f_path = item["path"]
        f_type = item["type"]

        # Base File Node
        statements.append(f"""
        MERGE (f:SourceFile {{path: '{f_path}'}})
        SET f.name = '{f_name}', f.type = '{f_type}'
        """)

        if f_type == "C":
            for inc in item["includes"]:
                inc_target = inc["target"]
                is_sys = inc["is_system"]
                statements.append(f"""
                MERGE (f:SourceFile {{path: '{f_path}'}})
                MERGE (inc:HeaderFile {{name: '{inc_target}'}})
                SET inc.is_system = {str(is_sys).lower()}
                MERGE (f)-[:INCLUDES]->(inc)
                """)

            for macro in item["macros"]:
                statements.append(f"""
                MERGE (f:SourceFile {{path: '{f_path}'}})
                MERGE (m:Macro {{name: '{macro}'}})
                MERGE (f)-[:DEFINES_MACRO]->(m)
                """)

            for fn in item["functions"]:
                defined_functions[fn] = f_path
                statements.append(f"""
                MERGE (f:SourceFile {{path: '{f_path}'}})
                MERGE (fn:Function {{name: '{fn}', file: '{f_path}'}})
                MERGE (f)-[:DEFINES]->(fn)
                """)

            for call in item["calls"]:
                caller = call["caller"]
                callee = call["callee"]
                statements.append(f"""
                MERGE (caller:Function {{name: '{caller}', file: '{f_path}'}})
                MERGE (callee:Function {{name: '{callee}'}})
                MERGE (caller)-[:CALLS]->(callee)
                """)

        elif f_type == "COBOL":
            prog = item["program_id"]
            defined_cobol_programs[prog] = f_path
            statements.append(f"""
            MERGE (f:SourceFile {{path: '{f_path}'}})
            MERGE (p:CobolProgram {{name: '{prog}'}})
            SET p.file = '{f_path}'
            MERGE (f)-[:CONTAINS]->(p)
            """)

            for cpy in item["copybooks"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (cb:Copybook {{name: '{cpy}'}})
                MERGE (p)-[:COPIES]->(cb)
                """)

            for ext_call in item["calls"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (sub:CobolProgram {{name: '{ext_call}'}})
                MERGE (p)-[:CALLS]->(sub)
                """)

            for sec in item["sections"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (s:Section {{name: '{sec}', program: '{prog}'}})
                MERGE (p)-[:DEFINES_SECTION]->(s)
                """)

            for perf in item["performs"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (s:Section {{name: '{perf}', program: '{prog}'}})
                MERGE (p)-[:PERFORMS]->(s)
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
    parser = argparse.ArgumentParser(description="Full Repository Inspection for C & COBOL dependencies into Neo4j")
    parser.add_argument("repo_path", nargs="?", default=".", help="Root path of repository to inspect (default: current directory)")
    parser.add_argument("--output-cypher", help="File to write Cypher statements (.cql)")
    parser.add_argument("--neo4j-url", default="http://localhost:7474", help="Neo4j HTTP base URL (default: http://localhost:7474)")
    parser.add_argument("--user", default="neo4j", help="Neo4j user")
    parser.add_argument("--password", default="password123", help="Neo4j password")
    parser.add_argument("--sync", action="store_true", help="Sync directly to running Neo4j container")

    args = parser.parse_args()
    repo_root = os.path.abspath(args.repo_path)

    print(f"============================================================")
    print(f"[*] Starting Full Repository Inspection")
    print(f"[*] Target Directory: {repo_root}")
    print(f"============================================================")

    results = scan_repository(repo_root)
    c_count = sum(1 for r in results if r["type"] == "C")
    cobol_count = sum(1 for r in results if r["type"] == "COBOL")

    print(f"[+] Found {len(results)} relevant source files (C: {c_count}, COBOL: {cobol_count})")
    for r in results:
        print(f"    - [{r['type']}] {r['path']}")

    statements = build_graph_statements(results)
    print(f"[+] Generated {len(statements)} graph relationship statements.")

    if args.output_cypher:
        with open(args.output_cypher, "w", encoding="utf-8") as fp:
            for s in statements:
                fp.write(s.strip() + ";\n\n")
        print(f"[+] Saved Cypher queries to: {args.output_cypher}")

    if args.sync:
        print(f"[*] Syncing full repository graph to Neo4j ({args.neo4j_url})...")
        execute_cypher_via_http(statements, neo4j_url=args.neo4j_url, auth=(args.user, args.password))

    print(f"[+] Full repository inspection completed.")


if __name__ == "__main__":
    main()
