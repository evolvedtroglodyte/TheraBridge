import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'auth_sessions'
    );
""")
exists = cur.fetchone()[0]

with open('migrations/analysis/auth_sessions_status.txt', 'w') as f:
    if exists:
        f.write('✅ auth_sessions table EXISTS\n')
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'auth_sessions'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        for col in cols:
            f.write(f"  - {col[0]}: {col[1]}\n")
    else:
        f.write('❌ auth_sessions table DOES NOT EXIST (needs creation)\n')

print(f"auth_sessions exists: {exists}")
cur.close()
conn.close()
