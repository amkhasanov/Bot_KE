import sqlite3

from settings import path_to_db

DB = sqlite3.connect(path_to_db, check_same_thread=False)
cur = DB.cursor()
#cur.execute("""ALTER TABLE chats ADD is_admin BOOLEAN DEFAULT(0) NOT NULL;""")
#cur.execute("""ALTER TABLE chats ADD subscription_date = CURRENT_TIMESTAMP;""")
cur.execute("""UPDATE chats SET is_admin = 1 WHERE chat_id IN (927060137, 430223218);""")
#cur.execute("""UPDATE chats SET subscription_date = CURRENT_TIMESTAMP;""")

DB.commit()
