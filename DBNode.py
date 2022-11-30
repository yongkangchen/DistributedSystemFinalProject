import sqlite3
import asyncio

class DBNode:
   con = None
   lock = asyncio.Lock()

   def __syncExecute__(*args):
      cur = DBNode.con.cursor()
      cur.execute(*args);
      DBNode.con.commit()
      count = cur.rowcount
      cur.close()
      return count

   def __syncQuery__(*args):
      cur = DBNode.con.cursor()
      res = cur.execute(*args);
      ret = res.fetchone()
      cur.close()

      if not ret: return None
      return ret[0]

   async def __execute__(*args):
      async with DBNode.lock:
         return await asyncio.get_running_loop().run_in_executor(None, DBNode.__syncExecute__, *args)

   def __query__(*args):
      return asyncio.get_running_loop().run_in_executor(None, DBNode.__syncQuery__, *args)

   def init(_, name = "test"):
      con = sqlite3.connect(name + ".db", check_same_thread=False)
      
      cur = con.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS DBNode(name, value)");
      con.commit()
      cur.close()

      DBNode.con = con


   def get(key: str) -> str:
      """Get the value of key.
      Returns:
         the value of key, or None when key does not exist.
      Raises:
         Error: An error is returned if the value stored
         at key is not a string, because GET only handles string
      values. """
      return DBNode.__query__("SELECT value FROM DBNode WHERE name = ?", (key,))
      
      
   async def set(key: str, value: str) -> bool:
      """Set key to hold the string value. If key already
      holds a value, it is overwritten, regardless of its type.
      Returns:
      True if SET was executed correctly.
      False if the key did not exist.
      """
      await DBNode.__execute__("REPLACE INTO DBNode(name, value) VALUES(?, ?)", (key, value));
      return True


   def delete(key: str) -> int:
      """Removes the specified keys. A key is ignored if it
      does not exist.
      Returns:
      The number of keys that were removed.
      """
      return DBNode.__execute__("DELETE FROM DBNode WHERE name= ? ", (key,))

   def command(cmd, key, timestamp, *args) -> any:
      cmd = cmd.upper()
      if cmd == "GET":
         return DBNode.get(key)

      elif cmd == "SET":
         return DBNode.set(key, *args)

      elif cmd == "DELETE":
         return DBNode.delete(key)
      
      return "Invalid query"