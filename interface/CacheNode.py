class CacheNode:
	def command(cmd: str, key: str, timestamp: int, *args) -> any:
		"""If data cached in this node and update time
		greater or equal than timestamp, return the cached data.
		Or Forward the command, key, args to the db node selected
		by the hash id of key mod max number of node, and store
		the result data and timestamp in cache. (TODO: Call
		NameService.select to get the id of db node)
		
		Args:
			cmd: A function name in DB Node such as GET and SET.
			key: A name of data stored in database or cache.
			timestamp: The latest update time of the data related to the key.
			args: other args of the command.

		Returns:
			The result returned by cache or db node.
		"""
		pass