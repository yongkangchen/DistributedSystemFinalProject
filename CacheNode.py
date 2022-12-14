from RPCFactory import RPCFactory
from collections import OrderedDict
import time
import config

class CacheNode:
    db_node = None
    nameservice = None
    nid = None
    capacity = None
    cache = None

    async def init(nid):
        db_addr = "tcp://" + config.DBNodeAddr + ":" + str(config.DBNodePort)
        name_service_addr = "tcp://" + config.NameServiceAddr + ":" + str(config.NameServicePort)

        await CacheNode.set_up(db_addr, name_service_addr, nid, 5000)

    async def set_up(db_addr: str, name_service_addr: str, nid: str, capacity: int) -> bool:
        CacheNode.db_node = db_addr
        CacheNode.nameservice = name_service_addr
        CacheNode.nid = nid
        CacheNode.capacity = capacity
        CacheNode.cache = OrderedDict()  # example: {"key": {"data":"aaaaaa", "timestamp": 1}}
        await RPCFactory.getInstance(CacheNode.nameservice).notify.register(CacheNode.nid)
        return True
    
    def __del__():
        asyncio.run(RPCFactory.getInstance(CacheNode.nameservice).unregister(CacheNode.nid))

    def generateNewTimetamp():
        return int(time.time())

    async def get(key: str, timestamp: int) -> str:
        data = None
        if key in CacheNode.cache:
            cur_timestamp = CacheNode.cache[key]["timestamp"]
            if timestamp > cur_timestamp or timestamp == -1:    # update the cache if the timestamp expired
                del CacheNode.cache[key]
            else:
                data = CacheNode.cache[key]["data"]

        if not data:
            data = await RPCFactory.getInstance(CacheNode.db_node).get(key)  # get data from DB

            if not data: return

            if len(CacheNode.cache) == CacheNode.capacity:
                CacheNode.cache.popitem(last=False)   # Remove the oldest item in the cache

            new_timestamp = CacheNode.generateNewTimetamp()
            CacheNode.cache[key] = {}    # add new data in cache
            CacheNode.cache[key]["data"] = data
            CacheNode.cache[key]["timestamp"] = new_timestamp
            await RPCFactory.getInstance(CacheNode.nameservice).notify.set_cache_meta(CacheNode.nid, key, new_timestamp)

        CacheNode.cache.move_to_end(key, last=True) # refresh to the newest order

        return data

    async def set(key: str, value: str) -> bool:
        await RPCFactory.getInstance(CacheNode.db_node).notify.set(key, value) # set value in DB

        new_timestamp = CacheNode.generateNewTimetamp()

        if key not in CacheNode.cache:
            if len(CacheNode.cache) == CacheNode.capacity:  
                CacheNode.cache.popitem(last=False)   # Remove the oldest item in the cache
            CacheNode.cache[key] = {}    # add new data in cache
        
        CacheNode.cache[key]["data"] = value
        CacheNode.cache[key]["timestamp"] = new_timestamp
        CacheNode.cache.move_to_end(key, last=True)

        await RPCFactory.getInstance(CacheNode.nameservice).notify.set_cache_meta(CacheNode.nid, key, new_timestamp)

        return True

    async def delete(key: str) -> bool:
        if key in CacheNode.cache:
            await RPCFactory.getInstance(CacheNode.db_node).notify.delete(key) # delete value in DB
            del CacheNode.cache[key]
            await RPCFactory.getInstance(CacheNode.nameservice).notify.set_cache_meta(CacheNode.nid, key, -1) # set the timestamp expired
            return True

        return False

    def heart_beat(check_num: int) -> int:
        return check_num

    def command(cmd: str, key: str, timestamp: str, *args) -> any:
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
            return CacheNode.get(key, timestamp)

        elif cmd == "SET":
            return CacheNode.set(key, args[0])

        elif cmd == "DELETE":
            return CacheNode.delete(key)
        
