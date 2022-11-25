import sqlite3
class DBNode:
    def ini():
     conn = sqlite3.connect('test.db')
     cur = conn.cursor()
     res = cur.execute("CREATE TABLE store(key,value)")  # table
     cur.close
     conn.commit()


    def get(key: str) -> str:
     conn = sqlite3.connect('test.db')
     cur = conn.cursor()
     res = cur.execute("SELECT value from store where key = ?",(key,))  # table name is store.
     cur.close
     conn.commit()
     return res.fetchall()


    def set(key: str, value: str) -> bool:
     conn = sqlite3.connect('test.db')
     cur = conn.cursor()
     test = cur.execute("SELECT * FROM store WHERE key=?", (key,))
     if test.fetchone() is None:
        cur.execute("INSERT INTO store VALUES(?,?)", (key, value,))
        return False
     else:
        cur.execute("UPDATE store SET value = ? where key= ?", (value, key,))
     cur.close
     conn.commit()
     return True


    def delete(key: str) -> int:
     conn = sqlite3.connect('test.db')
     cur = conn.cursor()
     test = cur.execute("SELECT value FROM store WHERE key=?", (key,))
     if test.fetchone() is None:
         return 0
     cur.execute(" DELETE FROM store where key= ? ", (key,))
     cur.close
     conn.commit()
     return 1
