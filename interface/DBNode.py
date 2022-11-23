class DBNode:
	db = {}
	def get(key: str) -> str:
		"""Get the value of key.
		Returns:
			the value of key, or None when key does not exist.
		Raises:
		    Error: An error is returned if the value stored
			at key is not a string, because GET only handles string
		values. """
		return DBNode.db.get(key, None)

	def set(key: str, value: str) -> bool:
		"""Set key to hold the string value. If key already
		holds a value, it is overwritten, regardless of its type.
		Returns:
		True if SET was executed correctly.
		False if the key did not exist.
		"""
		DBNode.db[key] = value
		return True


	def delete(*args) -> int:
		"""Removes the specified keys. A key is ignored if it
		does not exist.
		Returns:
		The number of keys that were removed.
		"""
		n = 0
		for key in args:
			if key not in DBNode.db: continue
			n += 1
			del DBNode.db[key]
		return n

	def command(cmd, key, timestamp, *args) -> any:
		cmd = cmd.upper()
		if cmd == "GET":
			return DBNode.get(key)

		elif cmd == "SET":
			return DBNode.set(key, *args)

		elif cmd == "DELETE":
			return DBNode.delete(key)
		
		return "Invalid query"