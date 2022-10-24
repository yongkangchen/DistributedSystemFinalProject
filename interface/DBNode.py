class DBNode:
	def get(key: str) -> str:
		"""Get the value of key.
		Returns:
			the value of key, or None when key does not exist.
		Raises:
		    Error: An error is returned if the value stored
			at key is not a string, because GET only handles string
		values. """

	def set(key: str, value: str) -> bool:
		"""Set key to hold the string value. If key already
		holds a value, it is overwritten, regardless of its type.
		Returns:
		True if SET was executed correctly.
		False if the key did not exist.
		"""
		pass

	def delete(key: str, *args) -> int:
		"""Removes the specified keys. A key is ignored if it
		does not exist.
		Returns:
		The number of keys that were removed.
		"""
		pass