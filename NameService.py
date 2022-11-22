import random
import asyncio

class NameService:

    def __init__(self):
        self.nodeList = []
        self.nodeDict = {}
        self.alive_node_set= set()
        self.failed_node_set= set()
        self.returned_heart_beat_node = set()

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

        if len(NameService.nodeList) == 0: return

        if key not in nodeDict:
            #TODO: select by heartbeat latency of node
            return NameService.nodeList[0], 0

        meta = nodeDict[key]
        if for_update:
            meta.clear()
            #TODO: mapping key
            return NameService.nodeList[0], 0

        return meta.items()[0]

    def register(nid: str) -> None:
        """Add a new node to the node list.

        Args:
            key: A identifier of a node.
        """
        NameService.nodeList.append(nid)

    def unregister(nid: str) -> None:
        """Remove a node from node list.
        """
        if nid not in NameService.nodeList: return
        NameService.nodeList.remove(nid)

    def set_cache_meta(nid: str, key: str, timestamp: int) -> None: 
        """Record the key cached in a node with its cached timestamp.
        """
        if key not in nodeDict: NameService.nodeDict[key] = {}
        NameService.nodeDict[key][nid] = timestamp

    def remove_alive_node(self, node):
        if node in self.alive_node_set:
            self.alive_node_set.remove(node)

        self.failed_node_set.add(node)

    def add_alive_node(self, node):
        if node in self.failed_node_set:
            self.failed_node_set.remove(node)

        self.alive_node_set.add(node)

    async def send_heart_beat(self, node, check_num): 
        return node.heart_beat(check_num)    # send a heart beat to a node 

    # TODO: One namservice node sends all hearbeats to different nodes or do this with multiple namservice node?
    async def check_heart_beat(self, node, timeout, period):  # node can be cache or load balancer
        try:
            check_num = random.randrange(1,100)
            return_num = check_num

            while check_num == return_num:      # The received number should be the same as the sent number
                self.add_alive_node(node)
                await asyncio.sleep(period)                  # send a heart bear periodly
                check_num = random.randrange(1,100)
                # asynchrous wait for response, if there is timeout then the node may has problems
                return_num = await asyncio.wait_for(send_heart_beat(node, check_num), timeout=timeout)

            self.remove_alive_node(node)
            self.returned_heart_beat_node.add(node)

        except asyncio.TimeoutError:
            self.remove_alive_node(node)
            self.returned_heart_beat_node.add(node)

    async def check_all_heartbeat(self):
        timeout = 60
        period = 60

        while self.returned_heart_beat_node:
            key, node = self.returned_heart_beat_node.pop()
            asyncio.run(check_heart_beat(node, timeout, period))


    def start_check_all_heartbeat(self):
        loop = asyncio.get_event_loop()
        self.returned_heart_beat_node = set.union(*self.nodeDict.values())
        self.alive_node_set = self.returned_heart_beat_node.copy()

        try:
            asyncio.ensure_future(check_all_heartbeat(), loop=loop)
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            print("Closing Loop")
            loop.close()



