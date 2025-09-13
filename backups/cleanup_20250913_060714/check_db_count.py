import sqlite3

conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM ingredients')
total = cursor.fetchone()[0]
print(f'Total ingredients: {total}')

cursor.execute('SELECT supplier_name, COUNT(*) FROM ingredients GROUP BY supplier_name ORDER BY COUNT(*) DESC LIMIT 5')
print('\nTop 5 suppliers:')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')

conn.close()