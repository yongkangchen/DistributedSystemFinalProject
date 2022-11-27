import random
import asyncio
import nest_asyncio
import time
import math

from RPCFactory import RPCFactory

nest_asyncio.apply()

class NameService:

    nodeList = []
    nodeDict = {}
    alive_node_dict = {}  # {nid: latency}
    returned_heart_beat_node = set()  # store failed or unchecked nodes

    def get_alive_node_dict() -> set:
        return list(NameService.alive_node_dict.keys())

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
        nodeList = NameService.nodeList

        if len(nodeList) == 0: return None, 0

        meta = NameService.nodeDict.get(key, None)
        if for_update:
            if meta: meta.clear()
            #TODO: mapping key
            return nodeList[0], 0

        alive_node_dict = NameService.alive_node_dict
        if not meta:
            if len(alive_node_dict) == 0: return nodeList[0], 0

            return min(alive_node_dict, key = alive_node_dict.get), 0

        id = max(nodeList, key = lambda nid: meta.get(nid, 0) - alive_node_dict.get(nid, 5000))

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
            del NameService.alive_node_dict[nid]
        finally:
            return True
        
        return True

    def set_cache_meta(nid: str, key: str, timestamp: int) -> None: 
        """Record the key cached in a node with its cached timestamp.
        """
        if key not in NameService.nodeDict: NameService.nodeDict[key] = {}
        NameService.nodeDict[key][nid] = timestamp

    def __send_heart_beat(node, check_num: int):
        return RPCFactory.getInstance(node).heart_beat(check_num)    # send a heart beat to a node 

    # TODO: One nameservice node sends all hearbeats to different nodes or do this with multiple namservice node?
    async def __check_heart_beat(node, timeout: int, period: int):  # node can be cache or load balancer
        try:
            check_num = random.randrange(1,100)
            return_num = check_num
            while check_num == return_num:      # The received number should be the same as the sent number
                check_num = random.randrange(1,100)
                # asynchrous wait for response, if there is timeout then the node may has problems
                start = time.time()
                return_num = await asyncio.wait_for(NameService.__send_heart_beat(node, check_num), timeout=timeout)
                end = time.time()
                NameService.alive_node_dict[node] = end - start # add lentency of an alive node
                await asyncio.sleep(period)                  # send a heart bear periodly
        finally:
            if node in NameService.alive_node_dict:
                del NameService.alive_node_dict[node]
            NameService.returned_heart_beat_node.add(node)

    async def __check_all_heartbeat():
        timeout = 3
        period = 5

        while True:
            while NameService.returned_heart_beat_node:
                node = NameService.returned_heart_beat_node.pop()
                asyncio.run(NameService.__check_heart_beat(node, timeout, period))
            await asyncio.sleep(period)

    def start_check_all_heartbeat() -> None:
        NameService.returned_heart_beat_node = set(NameService.nodeList)
        NameService.alive_node_dict = dict.fromkeys(NameService.returned_heart_beat_node, 5000)
        asyncio.create_task(NameService.__check_all_heartbeat())
