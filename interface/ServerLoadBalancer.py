import CacheNode
import NameService


class ServerLoadBalancer:
    def getCacheNode(key: str, for_update: bool = False)-> CacheNode:
        node_info = NameService.select(key, for_update)
        node = CacheNode(node_info)
        return node

    def forward(command: str, key: str, *args) -> any:
        """Call NameService.select to get the id and
        timestamp of cache node, and forward the command,
        key, timestamp, and args to the cache node.

        Args:
            command: A function name in DB Node such as GET and SET.
            key: A name of data stored in database or cache.
            args: other args of the command.
        Returns:
            The result returned by cache node.
        """
        node = ServerLoadBalancer.getCacheNode(key, command != "get")
        return node.command(command, key, node.timestamp, args)