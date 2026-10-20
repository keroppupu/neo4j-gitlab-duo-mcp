MERGE (f:SourceFile {path: 'analyzer/sample_code/db_utils.h'})
        SET f.name = 'db_utils.h', f.type = 'C';

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
        SET f.name = 'db_ops.pc', f.type = 'Pro*C';

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
                MERGE (inc:HeaderFile {name: 'stdio.h'})
                SET inc.is_system = true
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
                MERGE (inc:HeaderFile {name: 'db_utils.h'})
                SET inc.is_system = false
                MERGE (f)-[:INCLUDES]->(inc);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
                MERGE (fn:Function {name: 'fetch_employee', file: 'analyzer/sample_code/db_ops.pc'})
                MERGE (f)-[:DEFINES]->(fn);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
                    MERGE (t:DatabaseTable {name: 'EMP'})
                    MERGE (f)-[:ACCESSES_TABLE {action: 'SELECT'}]->(t);

MERGE (f:SourceFile {path: 'analyzer/sample_code/db_ops.pc'})
                    MERGE (t:DatabaseTable {name: 'SALARY'})
                    MERGE (f)-[:ACCESSES_TABLE {action: 'UPDATE'}]->(t);

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl'})
        SET f.name = 'BATCH01.cbl', f.type = 'COBOL';

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH01.cbl'})
            MERGE (p:CobolProgram {name: 'BATCH01'})
            SET p.file = 'analyzer/sample_code/BATCH01.cbl', p.is_procobol = false
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

MERGE (f:SourceFile {path: 'analyzer/sample_code/CUSTOMER.cpy'})
        SET f.name = 'CUSTOMER.cpy', f.type = 'COPYBOOK';

MERGE (f:SourceFile {path: 'analyzer/sample_code/CUSTOMER.cpy'})
            MERGE (cb:Copybook {name: 'CUSTOMER'})
            SET cb.file = 'analyzer/sample_code/CUSTOMER.cpy'
            MERGE (f)-[:CONTAINS]->(cb);

MERGE (cb:Copybook {name: 'CUSTOMER'})
                MERGE (cf:CopybookField {name: 'CUSTOMER-RECORD', copybook: 'CUSTOMER'})
                SET cf.level = '01', cf.pic = ''
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER'})
                MERGE (cf:CopybookField {name: 'CUST-ID', copybook: 'CUSTOMER'})
                SET cf.level = '05', cf.pic = 'X(10)'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER'})
                MERGE (cf:CopybookField {name: 'CUST-NAME', copybook: 'CUSTOMER'})
                SET cf.level = '05', cf.pic = 'X(40)'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

MERGE (cb:Copybook {name: 'CUSTOMER'})
                MERGE (cf:CopybookField {name: 'CUST-BALANCE', copybook: 'CUSTOMER'})
                SET cf.level = '05', cf.pic = 'S9(9)V99'
                MERGE (cb)-[:DEFINES_FIELD]->(cf);

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
                MERGE (callee:Function {name: 'close_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'init_db'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'process_data', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'add'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'process_data'})
                MERGE (caller)-[:CALLS]->(callee);

MERGE (caller:Function {name: 'main', file: 'analyzer/sample_code/main.c'})
                MERGE (callee:Function {name: 'printf'})
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
            SET p.file = 'analyzer/sample_code/SUBPROG1.cbl', p.is_procobol = false
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'SUBPROG1'})
                MERGE (s:Section {name: 'LINKAGE', program: 'SUBPROG1'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'SUBPROG1'})
                MERGE (s:Section {name: 'GOBACK', program: 'SUBPROG1'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH02.pco'})
        SET f.name = 'BATCH02.pco', f.type = 'Pro*COBOL';

MERGE (f:SourceFile {path: 'analyzer/sample_code/BATCH02.pco'})
            MERGE (p:CobolProgram {name: 'BATCH02'})
            SET p.file = 'analyzer/sample_code/BATCH02.pco', p.is_procobol = true
            MERGE (f)-[:CONTAINS]->(p);

MERGE (p:CobolProgram {name: 'BATCH02'})
                MERGE (cb:Copybook {name: 'CUSTOMER'})
                MERGE (p)-[:COPIES]->(cb);

MERGE (p:CobolProgram {name: 'BATCH02'})
                MERGE (s:Section {name: 'MAIN-LOGIC', program: 'BATCH02'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02'})
                MERGE (s:Section {name: 'FETCH-CUSTOMER-DATA', program: 'BATCH02'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02'})
                MERGE (s:Section {name: 'END-EXEC', program: 'BATCH02'})
                MERGE (p)-[:DEFINES_SECTION]->(s);

MERGE (p:CobolProgram {name: 'BATCH02'})
                MERGE (s:Section {name: 'FETCH-CUSTOMER-DATA', program: 'BATCH02'})
                MERGE (p)-[:PERFORMS]->(s);

MERGE (p:CobolProgram {name: 'BATCH02'})
                    MERGE (t:DatabaseTable {name: 'ACCOUNTS'})
                    MERGE (p)-[:ACCESSES_TABLE {action: 'SELECT'}]->(t);

MERGE (p:CobolProgram {name: 'BATCH02'})
                    MERGE (t:DatabaseTable {name: 'AUDIT_LOG'})
                    MERGE (p)-[:ACCESSES_TABLE {action: 'INSERT'}]->(t);

