MERGE (f:SourceFile {name: 'BATCH01.cbl'})
        SET f.path = '/Users/pupu/.gemini/antigravity/scratch/neo4j-gitlab-duo-mcp/analyzer/sample_code/BATCH01.cbl', f.type = 'COBOL';

MERGE (f:SourceFile {name: 'BATCH01.cbl'})
            MERGE (p:CobolProgram {name: 'BATCH01'})
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (sub:CobolProgram {name: 'LOGGER'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (sub:CobolProgram {name: 'SUBPROG1'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'MAIN-PROCEDURE'})
                MERGE (p)-[:DEFINES]->(s);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'CALC-SECTION'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'OUTPUT-SECTION'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (f:SourceFile {name: 'main.c'})
        SET f.path = '/Users/pupu/.gemini/antigravity/scratch/neo4j-gitlab-duo-mcp/analyzer/sample_code/main.c', f.type = 'C';

MERGE (f:SourceFile {name: 'main.c'})
                MERGE (inc:HeaderFile {name: 'stdio.h'})
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {name: 'main.c'})
                MERGE (inc:HeaderFile {name: 'db_utils.h'})
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {name: 'main.c'})
                MERGE (inc:HeaderFile {name: 'calculator.h'})
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {name: 'main.c'})
                MERGE (fn:Function {name: 'process_data'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {name: 'main.c'})
                MERGE (fn:Function {name: 'main'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (caller:Function {name: 'process_data'})
                MERGE (callee:Function {name: 'add'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data'})
                MERGE (callee:Function {name: 'close_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data'})
                MERGE (callee:Function {name: 'init_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main'})
                MERGE (callee:Function {name: 'process_data'})
                MERGE (caller)-[:CALLS]->(callee);

