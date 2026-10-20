MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.h'})
        SET f.name = 'db_utils.h', f.type = 'C';

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.h'})
                MERGE (m:Macro {name: 'DB_UTILS_H'})
                MERGE (f)-[:DEFINES_MACRO]->(m);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.h'})
                MERGE (m:Macro {name: 'MAX_CONNECTIONS'})
                MERGE (f)-[:DEFINES_MACRO]->(m);

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl'})
        SET f.name = 'BATCH01.cbl', f.type = 'COBOL';

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl'})
            MERGE (p:CobolProgram {name: 'BATCH01'})
            SET p.file = 'analyzer/sample_code/BATCH01.cbl'
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (sub:CobolProgram {name: 'LOGGER'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (sub:CobolProgram {name: 'SUBPROG1'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'MAIN-PROCEDURE', program: 'BATCH01'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'CALC-SECTION', program: 'BATCH01'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (p:CobolProgram {name: 'BATCH01'})
                MERGE (s:Section {name: 'OUTPUT-SECTION', program: 'BATCH01'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
        SET f.name = 'main.c', f.type = 'C';

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
                MERGE (inc:HeaderFile {name: 'stdio.h'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
                MERGE (inc:HeaderFile {name: 'db_utils.h'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
                MERGE (inc:HeaderFile {name: 'calculator.h'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
                MERGE (fn:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c'})
                MERGE (fn:Function {name: 'main', file: 'analyzer/sample_code/main.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (caller:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'add'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'init_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'close_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'printf'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'process_data'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c'})
        SET f.name = 'db_utils.c', f.type = 'C';

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c'})
                MERGE (inc:HeaderFile {name: 'db_utils.h'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c'})
                MERGE (inc:HeaderFile {name: 'stdio.h'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c'})
                MERGE (fn:Function {name: 'init_db', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c'})
                MERGE (fn:Function {name: 'close_db', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (caller:Function {name: 'init_db', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (callee:Function {name: 'printf'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'close_db', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (callee:Function {name: 'printf'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (f:SourceFile {path: 'analyzer/sample_code/SUBPROG1.cbl'})
        SET f.name = 'SUBPROG1.cbl', f.type = 'COBOL';

MERGE (f:SourceFile {path: 'analyzer/sample_code/SUBPROG1.cbl'})
            MERGE (p:CobolProgram {name: 'SUBPROG1'})
            SET p.file = 'analyzer/sample_code/SUBPROG1.cbl'
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'SUBPROG1'})
                MERGE (s:Section {name: 'LINKAGE', program: 'SUBPROG1'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'SUBPROG1'})
                MERGE (s:Section {name: 'GOBACK', program: 'SUBPROG1'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

