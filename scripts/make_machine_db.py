#!/usr/local/bin/python3.1

import os
import sys
import sqlite3 as db

def main(argv):
    if len(argv) < 3:
        usage()
        
    architecture = argv[1]
    processors = argv[2:]
    
    db_name = "{}.db".format(architecture)
    if os.path.exists(db_name):
        print("Attempting to remove %s..." % db_name)
        remove_db(db_name)
    
    print("Creating %s..." % db_name)    
    conn = db.connect(db_name)
    cursor = conn.cursor()
    for file in ('machine.ddl', os.path.join(architecture, 'registers.sql'),
                 'init.sql'):
        print("Reading %s..." % file)
        with open(file) as f:
            cursor.executescript(f.read())
    conn.commit()

    print('Running load_patterns.py...')
    load_patterns.load(db_name, os.path.join(architecture, 'patterns'))

    query = """
            insert into code_seq_by_processor (processor, code_seq_id)
            select ?, id
            from code_seq;
            """
    for p in processors:
        print("Adding processor %s..." % p)
        cursor.execute(query, (p, ))
    conn.commit()

def usage():
    sys.stderr.write("make_machine_db.py architecture processor...")
    sys.exit(2)

def remove_db(db_name):
    try:
        os.remove(db_name)
        print("%s removed." % db_name)
    except OSError as e:
        print("The database could not be removed due to the following error:")
        print(e)
        sys.exit(1)    

if __name__ == "__main__":
    from doctest_tools import setpath
    root_dir = setpath.setpath(__file__, remove_first=True)[0]
    codegen_dir = os.path.join(root_dir, 'ucc', 'codegen')
    print("Changing to", codegen_dir)
    os.chdir(codegen_dir)
    from ucc.codegen import load_patterns
    main(sys.argv)
