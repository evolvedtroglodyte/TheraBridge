import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, 
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """)
    
    with open('migrations/analysis/users_table_schema.txt', 'w') as f:
        f.write('USERS TABLE SCHEMA\n')
        f.write('='*80 + '\n\n')
        columns = cur.fetchall()
        for col in columns:
            name, dtype, max_len, nullable, default = col
            len_str = f"({max_len})" if max_len else ""
            f.write(f"{name:<30} {dtype}{len_str:<20} NULL:{nullable:<3} DEFAULT:{default}\n")
        f.write(f'\nTotal: {len(columns)} columns\n')
    
    print(f"✅ Exported {len(columns)} columns from users table")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
