import sqlite3

# Create alerts table for violence logs
conn1 = sqlite3.connect('violence_log.db')
cursor1 = conn1.cursor()
cursor1.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        video TEXT,
        frame_path TEXT,
        confidence REAL,
        timestamp TEXT
    )
''')
conn1.commit()
conn1.close()

# Create video logs table
conn2 = sqlite3.connect('video_logs.db')
cursor2 = conn2.cursor()
cursor2.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        filename TEXT,
        status TEXT,
        timestamp TEXT
    )
''')
conn2.commit()
conn2.close()

print("✅ Databases initialized successfully.")


