import os
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def backup_database():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    backup = {'timestamp': datetime.utcnow().isoformat(), 'tables': {}}

    tables = ['users', 'sessions']
    for table in tables:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f'SELECT * FROM {table};')
                rows = cur.fetchall()
                backup['tables'][table] = [dict(row) for row in rows]
                print(f"✅ Backed up {len(rows)} rows from {table}")
        except Exception as e:
            print(f"⚠️ Could not backup {table}: {e}")

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'migrations/backups/backup_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump(backup, f, indent=2, default=str)

    conn.close()
    print(f'✅ BACKUP SAVED: {filename}')
    return filename

if __name__ == '__main__':
    backup_database()
