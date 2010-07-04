import os
import sys
import sqlite3 as db

if __name__ == "__main__":
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first=True)
    from ucc.codegen import load_patterns

def usage():
	sys.stderr.write("make_machine_db architecture processor...")
	sys.exit(2)
	
def remove_db(db_name):
	try:
		os.remove(db_name)
		print("%s removed." % db_name)
	except OSError as e:
		print("The database could not be removed due to the following error:")
		print(e)
		sys.exit(1)

if len(sys.argv) < 3:
	usage()
	
architecture = sys.argv[1]
processor = sys.argv[2]
db_name = "%s.db" % architecture # basename?

if os.path.exists(db_name):
	print("Attepting to remove %s..." % db_name)
	remove_db(db_name)

print("Creating %s..." % db_name)

files = (
	'machine.ddl',
	os.path.join(architecture, 'registers.sql'),
	'init.sql'
)

conn = db.connect(db_name)
cursor = conn.cursor()
for file in files:
	print("Reading %s..." % file)
	f = open(file)
	queries = f.read().split(';')
	for q in queries:
		try:
			cursor.execute(q)
		except db.OperationalError as e:
			print('Exception: %s' % e)
			print('Query: %s' % q)
			sys.exit(1)
	print('OK')
conn.commit()

print('Running load_patterns.py...')
load_patterns.load(db_name, os.path.join(architecture, 'patterns'))

values = (processor, )
query = """
	insert into code_seq_by_processor (processor, code_seq_id)
	select ?, id
	from code_seq;
	"""
print("Adding processor %s..." % processor)
cursor.execute(query, values)
conn.commit()
