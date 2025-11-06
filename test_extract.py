import sqlite3

conn = sqlite3.connect('data/quran_v10.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type='table'
    AND name NOT LIKE 'sqlite_%'
    AND name != 'fastmigrate_meta'
    ORDER BY name
""")

tables = cursor.fetchall()

with open('schema_extracted.sql', 'w') as f:
    f.write(f"-- Extracted schema from data/quran_v10.db\n")
    f.write(f"-- Found {len(tables)} tables\n\n")

    for table_name, create_sql in tables:
        f.write(f"-- Table: {table_name}\n")
        f.write(f"{create_sql};\n\n")

print(f"Schema extracted to schema_extracted.sql ({len(tables)} tables)")
conn.close()
