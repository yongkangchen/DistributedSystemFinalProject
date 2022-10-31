from interface import DBNode
from collections import OrderedDict

class CacheNode:
	def __init__(self, capacity, nid, nameservice):
		self.cache = OrderedDict()  # example: {"key": {"data":"aaaaaa", "timestamp": 1}}
		self.capacity = capacity
		self.nid = nid
		self.nameservice = nameservice
		self.nameservice.register(self.nid)
	
	def __del__(self):
		self.nameservice.unregister(self.nid)

	def getDBNode(self, key: str, for_update: bool = False) -> DBNode:  # get a DB node 
		#node_info = NameService.select(key, for_update)

		#TODO: verify how to initialize a node class for next layers
		# node = DBNode(node_info)
		
		return DBNode(self.nid)

	def get(self, key: str, timestamp: int) -> str:
		data = None
		if key in self.cache:
			cur_timestamp = self.cache[key]["timestamp"]
			if timestamp > cur_timestamp or timestamp == -1:	# update the cache if the timestamp expired
				del self.cache[key]
			else:
				data = self.cache[key]["data"]

		if not data:
			data = self.getDBNode(key, False).get(key)  # get data from DB

			if not data: return

			if len(self.cache) == self.capacity:  
				self.cache.popitem(last=False)   # Remove the oldest item in the cache

			new_timestamp = self.generateNewTimetamp()
			self.cache[key] = {}	# add new data in cache
			self.cache[key]["data"] = data
			self.cache[key]["timestamp"] = new_timestamp
			self.nameservice.set_cache_meta(self.nid, key, new_timestamp)

		self.cache.move_to_end(key, last=True) # refresh to the newest order

		return data

	def set(self, key: str, value: str) -> bool:
		self.getDBNode(key, True).set(key, value) # set value in DB

		#TODO: verify how to generate the newest timestamp, we need the latest integer to do timestamp += 1,
		# but currently we don't know where to get 
		# the latest integer(sometimes timestamps from NameService is -1 or doesn't exist)
		#, or maybe we can use real time like 2022-10-29 20:00
		new_timestamp = self.generateNewTimetamp()

		if key not in self.cache:
			if len(self.cache) == self.capacity:  
				self.cache.popitem(last=False)   # Remove the oldest item in the cache
			self.cache[key] = {}	# add new data in cache
		
		self.cache[key]["data"] = value
		self.cache[key]["timestamp"] = new_timestamp    
		self.cache.move_to_end(key, last=True)

		self.nameservice.set_cache_meta(self.nid, key, new_timestamp)

		return True

	def delete(self, key: str) -> bool:
		self.getDBNode(key, True).delete(key) # delete value in DB

		if key in self.cache:
			del self.cache[key]

		self.nameservice.set_cache_meta(self.nid, key, -1) # set the timestamp expired

		return True


	def command(self, cmd: str, key: str, timestamp: int, *args) -> any:
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
		if cmd == "GET":
			return self.get(key, timestamp)

		elif cmd == "SET":
			return self.set(key, args[0])

		elif cmd == "DELETE":
			return self.delete(key)
		
		return "Invalid query"