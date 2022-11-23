#!python3

from RPCFactory import RPCFactory

class ServerLoadBalancer:
    NameService = None
    async def forward(command: str, key: str, *args) -> any:
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
        node_name, timestamp = await RPCFactory.getInstance(ServerLoadBalancer.NameService).select(key, command != "get")
        if not node_name: 
            #print("can not find node_name:", node_name, timestamp)
            return
        return await RPCFactory.getInstance(node_name).command(command, key, timestamp, *args)