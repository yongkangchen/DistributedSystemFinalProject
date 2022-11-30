#!python3

import sys, os, asyncio
from nng_json_rpc.RPCServer import RPCServer

from DBNode import DBNode
from CacheNode import CacheNode

from NameService import NameService

from ServerLoadBalancer import ServerLoadBalancer
import config

services = {
	NameService: config.NameServicePort,
	DBNode: config.DBNodePort,
	CacheNode: 0,
	ServerLoadBalancer: 0,
}

async def main(argv):
	size = len(argv)
	port = 0
	if size <= 1:
		print("usage: program service_name")
		print("\n".join([str(k.__name__) for k in services.keys()]))
		return
	
	name = argv[1].strip()

	service = None
	
	for k in services.keys():
		if name == k.__name__: 
			service = k
			break

	if not service:
		print("Invalid service name")
		return

	port = services[service]

	server = RPCServer("tcp://0.0.0.0:" + str(port))
	
	ret = service.init("tcp://" + str(server.local_address))
	if asyncio.iscoroutine(ret) or asyncio.isfuture(ret):
		await ret
	

	print("start service:", name, "local_address: ", server.local_address)
	server.build_method_map(service, name + ".")
	server.build_method_map(service)

	server.serve_forever()

if __name__ == "__main__":
	asyncio.run(main(sys.argv))
