MERGE (proj:Project {name: 'billing-system'});

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.h', project: 'billing-system'})
        SET f.name = 'db_utils.h', f.type = 'C'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
        SET f.name = 'db_ops.pc', f.type = 'Pro*C'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'stdio.h', project: 'billing-system'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'db_utils.h', project: 'billing-system'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
                MERGE (fn:Function {name: 'fetch_employee', project: 'billing-system', file: 'analyzer/sample_code/db_ops.pc'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
                    MERGE (t:DatabaseTable {name: 'EMP'})
                    MERGE (f)-[:ACCESSES_TABLE {action: 'SELECT', project: 'billing-system'}]->(t);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc', project: 'billing-system'})
                    MERGE (t:DatabaseTable {name: 'SALARY'})
                    MERGE (f)-[:ACCESSES_TABLE {action: 'UPDATE', project: 'billing-system'}]->(t);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl', project: 'billing-system'})
        SET f.name = 'BATCH01.cbl', f.type = 'COBOL'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl', project: 'billing-system'})
            MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
            SET p.file = 'analyzer/sample_code/BATCH01.cbl', p.is_procobol = false
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
                MERGE (sub:CobolProgram {name: 'SUBPROG1', project: 'billing-system'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
                MERGE (sub:CobolProgram {name: 'LOGGER', project: 'billing-system'})
                MERGE (p)-[:CALLS]->(sub);

MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
                MERGE (s:Section {name: 'MAIN-PROCEDURE', program: 'BATCH01', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
                MERGE (s:Section {name: 'CALC-SECTION', program: 'BATCH01', project: 'billing-system'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (p:CobolProgram {name: 'BATCH01', project: 'billing-system'})
                MERGE (s:Section {name: 'OUTPUT-SECTION', program: 'BATCH01', project: 'billing-system'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/CUSTOMER.cpy', project: 'billing-system'})
        SET f.name = 'CUSTOMER.cpy', f.type = 'COPYBOOK'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/CUSTOMER.cpy', project: 'billing-system'})
            MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
            SET cb.file = 'analyzer/sample_code/CUSTOMER.cpy'
            MERGE (f)-[:CONTAINS]->(cb);

MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
                MERGE (cf:CopybookField {name: 'CUSTOMER-RECORD', copybook: 'CUSTOMER', project: 'billing-system'})
                SET cf.level = '01', cf.pic = ''
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
                MERGE (cf:CopybookField {name: 'CUST-ID', copybook: 'CUSTOMER', project: 'billing-system'})
                SET cf.level = '05', cf.pic = 'X(10)'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
                MERGE (cf:CopybookField {name: 'CUST-NAME', copybook: 'CUSTOMER', project: 'billing-system'})
                SET cf.level = '05', cf.pic = 'X(40)'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
                MERGE (cf:CopybookField {name: 'CUST-BALANCE', copybook: 'CUSTOMER', project: 'billing-system'})
                SET cf.level = '05', cf.pic = 'S9(9)V99'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
        SET f.name = 'main.c', f.type = 'C'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'stdio.h', project: 'billing-system'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'db_utils.h', project: 'billing-system'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'calculator.h', project: 'billing-system'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
                MERGE (fn:Function {name: 'process_data', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/main.c', project: 'billing-system'})
                MERGE (fn:Function {name: 'main', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (caller:Function {name: 'process_data', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'init_db', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'close_db', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'add', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'printf', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', project: 'billing-system', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'process_data', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c', project: 'billing-system'})
        SET f.name = 'db_utils.c', f.type = 'C'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'db_utils.h', project: 'billing-system'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c', project: 'billing-system'})
                MERGE (inc:HeaderFile {name: 'stdio.h', project: 'billing-system'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c', project: 'billing-system'})
                MERGE (fn:Function {name: 'init_db', project: 'billing-system', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.c', project: 'billing-system'})
                MERGE (fn:Function {name: 'close_db', project: 'billing-system', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (caller:Function {name: 'init_db', project: 'billing-system', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (callee:Function {name: 'printf', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'close_db', project: 'billing-system', file: 'analyzer/sample_code/db_utils.c'})
                MERGE (callee:Function {name: 'printf', project: 'billing-system'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/SUBPROG1.cbl', project: 'billing-system'})
        SET f.name = 'SUBPROG1.cbl', f.type = 'COBOL'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/SUBPROG1.cbl', project: 'billing-system'})
            MERGE (p:CobolProgram {name: 'SUBPROG1', project: 'billing-system'})
            SET p.file = 'analyzer/sample_code/SUBPROG1.cbl', p.is_procobol = false
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'SUBPROG1', project: 'billing-system'})
                MERGE (s:Section {name: 'LINKAGE', program: 'SUBPROG1', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'SUBPROG1', project: 'billing-system'})
                MERGE (s:Section {name: 'GOBACK', program: 'SUBPROG1', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (proj:Project {name: 'billing-system'})
        MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH02.pco', project: 'billing-system'})
        SET f.name = 'BATCH02.pco', f.type = 'Pro*COBOL'
        MERGE (proj)-[:CONTAINS_FILE]->(f);

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH02.pco', project: 'billing-system'})
            MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
            SET p.file = 'analyzer/sample_code/BATCH02.pco', p.is_procobol = true
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                MERGE (cb:Copybook {name: 'CUSTOMER', project: 'billing-system'})
                MERGE (p)-[:COPIES]->(cb);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                MERGE (s:Section {name: 'MAIN-LOGIC', program: 'BATCH02', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                MERGE (s:Section {name: 'FETCH-CUSTOMER-DATA', program: 'BATCH02', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                MERGE (s:Section {name: 'END-EXEC', program: 'BATCH02', project: 'billing-system'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                MERGE (s:Section {name: 'FETCH-CUSTOMER-DATA', program: 'BATCH02', project: 'billing-system'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                    MERGE (t:DatabaseTable {name: 'ACCOUNTS'})
                    MERGE (p)-[:ACCESSES_TABLE {action: 'SELECT', project: 'billing-system'}]->(t);

MERGE (p:CobolProgram {name: 'BATCH02', project: 'billing-system'})
                    MERGE (t:DatabaseTable {name: 'AUDIT_LOG'})
                    MERGE (p)-[:ACCESSES_TABLE {action: 'INSERT', project: 'billing-system'}]->(t);

