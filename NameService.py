class NameService:
    nodeList = []
    nodeDict = {}

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