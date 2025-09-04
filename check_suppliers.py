import sqlite3

conn = sqlite3.connect('daham_meal.db')
print('Suppliers in database:')
suppliers = conn.execute('SELECT * FROM suppliers').fetchall()
for supplier in suppliers:
    print(supplier)
    
print(f'\nTotal suppliers: {len(suppliers)}')
conn.close()