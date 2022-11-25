import random
import asyncio
from RPCFactory import RPCFactory
import nest_asyncio

nest_asyncio.apply()

class NameService:

    nodeList = []
    nodeDict = {}
    alive_node_set = set()
    failed_node_set = set()
    returned_heart_beat_node = set()

    def get_alive_node_set() -> set:
        return list(NameService.alive_node_set)

    def select(key: str, for_update: bool = False) -> tuple[str, int]:
        """Get the fast node in the register list which
        cached the data of the key. If a node didn’t cache the key 
        but is faster than a node cached the key over the
        average time of handled operation of missed cache. Then
        should return the node even it didn’t cache the key.

        Args:
            key: A key of value saved in the database.
            for_update: Indicate if the node used for update.

        Returns:
            The id of a node and the timestamp of the key, or None when there does not exist any available node.
        """

        if len(NameService.nodeList) == 0: return None, 0

        if key not in NameService.nodeDict:
            #TODO: select by heartbeat latency of node
            return NameService.nodeList[0], 0

        meta = NameService.nodeDict[key]
        if for_update:
            meta.clear()
            #TODO: mapping key
            return NameService.nodeList[0], 0

        #TODO: select by heartbeat latency of node
        id = max(NameService.nodeList, key=lambda nid: meta.get(nid, 0))
        return id, meta.get(id, 0)

    def register(nid: str) -> None:
        """Add a new node to the node list.

        Args:
            key: A identifier of a node.
        """
        NameService.nodeList.append(nid)
        NameService.returned_heart_beat_node.add(nid)

    def unregister(nid: str) -> bool:
        """Remove a node from node list.
        """
        if nid not in NameService.nodeList: return False
        NameService.nodeList.remove(nid)

        try:
            NameService.returned_heart_beat_node.remove(nid)
            NameService.alive_node_set.remove(nid)
            NameService.failed_node_set.remove(nid)
        finally:
            return True
        
        return True

    def set_cache_meta(nid: str, key: str, timestamp: int) -> None: 
        """Record the key cached in a node with its cached timestamp.
        """
        if key not in NameService.nodeDict: NameService.nodeDict[key] = {}
        NameService.nodeDict[key][nid] = timestamp

    def remove_alive_node(node):
        if node in NameService.alive_node_set:
            NameService.alive_node_set.remove(node)

        NameService.failed_node_set.add(node)

    def add_alive_node(node):
        if node in NameService.failed_node_set:
            NameService.failed_node_set.remove(node)

        NameService.alive_node_set.add(node)

    async def send_heart_beat(node, check_num: int): 
        return await RPCFactory.getInstance(node).heart_beat(check_num)    # send a heart beat to a node 

    # TODO: One nameservice node sends all hearbeats to different nodes or do this with multiple namservice node?
    async def check_heart_beat(node, timeout: int, period: int):  # node can be cache or load balancer
        try:
            check_num = random.randrange(1,100)
            return_num = check_num

            while check_num == return_num:      # The received number should be the same as the sent number
                check_num = random.randrange(1,100)
                # asynchrous wait for response, if there is timeout then the node may has problems
                return_num = await asyncio.wait_for(NameService.send_heart_beat(node, check_num), timeout=timeout)
                NameService.add_alive_node(node)
                await asyncio.sleep(period)                  # send a heart bear periodly

            NameService.remove_alive_node(node)
            NameService.returned_heart_beat_node.add(node)

        except:
            NameService.remove_alive_node(node)
            NameService.returned_heart_beat_node.add(node)

    async def check_all_heartbeat():
        timeout = 3
        period = 5

        while True:
            while NameService.returned_heart_beat_node:
                node = NameService.returned_heart_beat_node.pop()
                asyncio.run(NameService.check_heart_beat(node, timeout, period))

            await asyncio.sleep(period)


    def start_check_all_heartbeat() -> None:
        NameService.returned_heart_beat_node = set(NameService.nodeList)
        NameService.alive_node_set = NameService.returned_heart_beat_node.copy()
        asyncio.create_task(NameService.check_all_heartbeat())
