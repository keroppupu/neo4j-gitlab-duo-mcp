#!/usr/bin/env python3
"""
C & COBOL Static Dependency Analyzer for Neo4j Knowledge Graph.

Parses C and COBOL source files, extracts structural relationships (File, Function/Section, Program),
and writes Cypher queries or directly registers them into Neo4j via HTTP/Bolt.
"""

import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path


class CParser:
    """Parses C source code for includes, function definitions, and function calls."""
    
    INCLUDE_REGEX = re.compile(r'#include\s*["<]([^">]+)[">]')
    # Simple regex for C function definitions: return_type func_name(args) { ... }
    FUNC_DEF_REGEX = re.compile(
        r'^[ \t]*(?:static\s+|inline\s+)?(?:[a-zA-Z_][a-zA-Z0-9_* \t]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{',
        re.MULTILINE
    )
    # Simple regex for function calls: func_name(args)
    FUNC_CALL_REGEX = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
    KEYWORDS = {'if', 'for', 'while', 'switch', 'return', 'sizeof', 'printf', 'fprintf', 'scanf'}

    def parse(self, file_path: str, content: str):
        file_name = os.path.basename(file_path)
        data = {
            "type": "C",
            "file": file_name,
            "path": file_path,
            "includes": [],
            "functions": [],
            "calls": []  # (caller_func, callee_func)
        }

        # 1. Extract includes
        for line in content.splitlines():
            inc = self.INCLUDE_REGEX.findall(line)
            if inc:
                data["includes"].extend(inc)

        # 2. Extract function definitions and line boundaries
        matches = list(self.FUNC_DEF_REGEX.finditer(content))
        for i, match in enumerate(matches):
            func_name = match.group(1)
            if func_name in self.KEYWORDS:
                continue
            start_pos = match.end()
            # Estimate body end
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            func_body = content[start_pos:end_pos]

            data["functions"].append(func_name)

            # 3. Extract calls within function body
            calls = set(self.FUNC_CALL_REGEX.findall(func_body))
            for callee in calls:
                if callee not in self.KEYWORDS and callee != func_name:
                    data["calls"].append({"caller": func_name, "callee": callee})

        return data


class CobolParser:
    """Parses COBOL source code for PROGRAM-ID, COPY, CALL, and PERFORM."""

    PROGRAM_ID_REGEX = re.compile(r'PROGRAM-ID\.\s*([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    COPY_REGEX = re.compile(r'\bCOPY\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    CALL_REGEX = re.compile(r'\bCALL\s+["\']([a-zA-Z0-9_\-]+)["\']', re.IGNORECASE)
    PERFORM_REGEX = re.compile(r'\bPERFORM\s+([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    SECTION_REGEX = re.compile(r'^[ \t]*([a-zA-Z0-9_\-]+)\s*(?:SECTION|PROCEDURE)?\.\s*$', re.MULTILINE | re.IGNORECASE)
    RESERVED = {'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE', 'DIVISION', 'WORKING-STORAGE', 'STOP'}

    def parse(self, file_path: str, content: str):
        file_name = os.path.basename(file_path)
        prog_match = self.PROGRAM_ID_REGEX.search(content)
        program_id = prog_match.group(1).upper() if prog_match else file_name.rsplit('.', 1)[0].upper()

        data = {
            "type": "COBOL",
            "file": file_name,
            "path": file_path,
            "program_id": program_id,
            "copybooks": [],
            "calls": [],      # external program calls
            "sections": [],   # internal sections / paragraphs
            "performs": []    # internal performs
        }

        # Clean line numbers if present in fixed format (cols 1-6)
        cleaned_lines = []
        for line in content.splitlines():
            # If line starts with 6 digits, strip them
            if re.match(r'^\d{6}', line):
                line = line[6:]
            cleaned_lines.append(line)
        cleaned_content = "\n".join(cleaned_lines)

        # 1. Extract COPY statements
        data["copybooks"] = list(set(self.COPY_REGEX.findall(cleaned_content)))

        # 2. Extract CALL statements (External subprograms)
        data["calls"] = list(set(self.CALL_REGEX.findall(cleaned_content)))

        # 3. Extract sections / paragraphs
        for m in self.SECTION_REGEX.finditer(cleaned_content):
            sec_name = m.group(1).strip().upper()
            if sec_name not in self.RESERVED and not sec_name.endswith('-SECTION') and sec_name not in data["sections"]:
                data["sections"].append(sec_name)

        # 4. Extract PERFORM statements
        for m in self.PERFORM_REGEX.finditer(cleaned_content):
            target = m.group(1).strip().upper()
            if target not in self.RESERVED and target not in data["performs"]:
                data["performs"].append(target)

        return data


def generate_cypher_statements(analysis_results):
    """Converts parsed structural metadata into Cypher queries."""
    statements = []

    for item in analysis_results:
        f_name = item["file"]
        f_type = item["type"]
        f_path = item["path"]

        # Node: File
        statements.append(f"""
        MERGE (f:SourceFile {{name: '{f_name}'}})
        SET f.path = '{f_path}', f.type = '{f_type}'
        """)

        if f_type == "C":
            # Includes
            for inc in item["includes"]:
                statements.append(f"""
                MERGE (f:SourceFile {{name: '{f_name}'}})
                MERGE (inc:HeaderFile {{name: '{inc}'}})
                MERGE (f)-[:INCLUDES]->(inc)
                """)

            # Functions defined
            for func in item["functions"]:
                statements.append(f"""
                MERGE (f:SourceFile {{name: '{f_name}'}})
                MERGE (fn:Function {{name: '{func}'}})
                MERGE (f)-[:DEFINES]->(fn)
                """)

            # Function calls
            for call in item["calls"]:
                caller = call["caller"]
                callee = call["callee"]
                statements.append(f"""
                MERGE (caller:Function {{name: '{caller}'}})
                MERGE (callee:Function {{name: '{callee}'}})
                MERGE (caller)-[:CALLS]->(callee)
                """)

        elif f_type == "COBOL":
            prog = item["program_id"]
            statements.append(f"""
            MERGE (f:SourceFile {{name: '{f_name}'}})
            MERGE (p:CobolProgram {{name: '{prog}'}})
            MERGE (f)-[:CONTAINS]->(p)
            """)

            # Copybooks
            for cpy in item["copybooks"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (cb:Copybook {{name: '{cpy}'}})
                MERGE (p)-[:COPIES]->(cb)
                """)

            # External CALLs
            for ext_call in item["calls"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (sub:CobolProgram {{name: '{ext_call}'}})
                MERGE (p)-[:CALLS]->(sub)
                """)

            # Internal Sections & Performs
            for sec in item["sections"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (s:Section {{name: '{sec}'}})
                MERGE (p)-[:DEFINES]->(s)
                """)

            for perf in item["performs"]:
                statements.append(f"""
                MERGE (p:CobolProgram {{name: '{prog}'}})
                MERGE (s:Section {{name: '{perf}'}})
                MERGE (p)-[:PERFORMS]->(s)
                """)

    return statements


def execute_cypher_via_http(statements, neo4j_url="http://localhost:7474", auth=("neo4j", "password123")):
    """Executes Cypher statements against Neo4j HTTP API transaction endpoint."""
    endpoint = f"{neo4j_url.rstrip('/')}/db/neo4j/tx/commit"
    
    # Format for Neo4j HTTP transaction API
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
            print(f"[+] Successfully executed {len(tx_statements)} statements in Neo4j.")
            return True
    except urllib.error.URLError as e:
        print(f"[-] Could not connect to Neo4j HTTP API at {endpoint}: {e}")
        return False


def scan_directory(target_dir):
    c_parser = CParser()
    cobol_parser = CobolParser()
    results = []

    c_exts = {'.c', '.h', '.cpp', '.hpp', '.cc'}
    cobol_exts = {'.cbl', '.cob', '.cpy', '.cobol'}

    for root, _, files in os.walk(target_dir):
        for f in files:
            path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
            except Exception as e:
                print(f"[-] Failed to read {path}: {e}")
                continue

            if ext in c_exts:
                results.append(c_parser.parse(path, content))
            elif ext in cobol_exts:
                results.append(cobol_parser.parse(path, content))

    return results


def main():
    parser = argparse.ArgumentParser(description="Analyze C & COBOL dependencies into Neo4j knowledge graph")
    parser.add_argument("target_dir", help="Directory path containing source code to analyze")
    parser.add_argument("--output-cypher", help="File path to save generated Cypher queries (.cql)")
    parser.add_argument("--neo4j-url", default="http://localhost:7474", help="Neo4j HTTP base URL (default: http://localhost:7474)")
    parser.add_argument("--user", default="neo4j", help="Neo4j user")
    parser.add_argument("--password", default="password123", help="Neo4j password")
    parser.add_argument("--sync", action="store_true", help="Directly sync to running Neo4j container via HTTP API")

    args = parser.parse_args()

    print(f"[*] Scanning directory: {args.target_dir} for C and COBOL files...")
    results = scan_directory(args.target_dir)
    print(f"[+] Analyzed {len(results)} source files.")

    statements = generate_cypher_statements(results)
    print(f"[+] Generated {len(statements)} Cypher relationship statements.")

    if args.output_cypher:
        with open(args.output_cypher, "w", encoding="utf-8") as fp:
            for s in statements:
                fp.write(s.strip() + ";\n\n")
        print(f"[+] Saved Cypher queries to: {args.output_cypher}")

    if args.sync:
        print(f"[*] Syncing to Neo4j ({args.neo4j_url})...")
        execute_cypher_via_http(statements, neo4j_url=args.neo4j_url, auth=(args.user, args.password))

    print("[+] Done!")


if __name__ == "__main__":
    main()
