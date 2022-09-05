import sqlite3

DB = sqlite3.connect('sqlite_bot.db', check_same_thread=False)
cur = DB.cursor()
cur.execute("""ALTER TABLE chats ADD is_admin BOOLEAN DEFAULT(0) NOT NULL;
       ALTER TABLE ADD subscription_date TIMESTAMP DEFAULT(datetime('now', 'localtime'));
    """)
DB.commit()