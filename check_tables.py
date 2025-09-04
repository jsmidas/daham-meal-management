import sqlite3

conn = sqlite3.connect('daham_meal.db')
print('Tables in database:')
for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    print(f'- {table[0]}')
    
print('\nChecking for sample/default data...')
tables_to_check = ['business_locations', 'suppliers', 'ingredients', 'menu_recipes']

for table in tables_to_check:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f'{table}: {count} records')
        if count > 0 and count < 5:  # Show first few records
            records = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchall()
            for record in records:
                print(f'  {record}')
    except Exception as e:
        print(f'{table}: Table not found or error - {e}')

conn.close()