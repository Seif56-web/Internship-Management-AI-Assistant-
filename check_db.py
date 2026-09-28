import sqlite3

conn = sqlite3.connect(r'D:\gestion_des_stagiaires_backup\backend\gestion_stagiaires.db')
cursor = conn.cursor()

# List tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)

# Check evaluations table
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="evaluations"')
eval_schema = cursor.fetchone()
print('Evaluations schema:', eval_schema)

# Check stagiaires table
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="stagiaires"')
stag_schema = cursor.fetchone()
print('Stagiaires schema:', stag_schema)

# Count evaluations
cursor.execute('SELECT COUNT(*) FROM evaluations')
eval_count = cursor.fetchone()
print('Evaluation count:', eval_count)

# Check evaluations data
cursor.execute('SELECT * FROM evaluations')
evals = cursor.fetchall()
print('Evaluations data:', evals)

# Count stagiaires
cursor.execute('SELECT COUNT(*) FROM stagiaires')
stag_count = cursor.fetchone()
print('Stagiaire count:', stag_count)

# Check stagiaires data
cursor.execute('SELECT id, nom_complet, cin, encadrant_id FROM stagiaires')
stags = cursor.fetchall()
print('Stagiaires data:', stags)

# Check users
cursor.execute('SELECT id, email, role FROM users')
users = cursor.fetchall()
print('Users:', users)

conn.close()