#!python3

from RPCClient import ServerProxy
import asyncio

from threading import Thread

def startService(service):
	from RPCServer import RPCServer
	server = RPCServer("tcp://127.0.0.1:0")
	local_address = server.local_address

	server.build_method_map(service, service.__name__ + ".")
	server.build_method_map(service)

	asyncio.create_task(server.start())

	return local_address

async def testDBNode():
	from interface.DBNode import DBNode
	local_address = startService(DBNode)

	svr = ServerProxy("tcp://" + str(local_address)).DBNode
		
	assert(await svr.command("GET", "name", 0) == None)
	

	assert(await svr.command("SET", "name", 0, "cyk") == True)
	assert(await svr.command("GET", "name", 0) == "cyk")

	assert(await svr.command("DELETE", "name", 0) == 1)
	assert(await svr.command("GET", "name", 0) == None)

	assert(await svr.command("DELETE", "name", 0) == 0)
	

async def testNameService():
	from NameService import NameService
	local_address = startService(NameService)

	svr = ServerProxy("tcp://" + str(local_address)).NameService

	assert(await svr.unregister("localhost:8080") in [True, False])
	assert(await svr.unregister("localhost:8081") in [True, False])
	assert(await svr.unregister("localhost:8082") in [True, False])

	assert(await svr.select("name") == [None, 0])

	assert(await svr.register("localhost:8080") == None)

	assert(await svr.select("name") == ["localhost:8080", 0])
	assert(await svr.set_cache_meta("localhost:8081", "name", 1) == None)
	assert(await svr.select("name") == ["localhost:8080", 0])

	assert(await svr.register("localhost:8081") == None)
	assert(await svr.set_cache_meta("localhost:8081", "name", 1) == None)
	assert(await svr.select("name") == ["localhost:8081", 1])

	assert(await svr.set_cache_meta("localhost:8081", "name", 2) == None)
	assert(await svr.select("name") == ["localhost:8081", 2])

	assert(await svr.set_cache_meta("localhost:8082", "name", 3) == None)
	assert(await svr.select("name") == ["localhost:8081", 2])
	assert(await svr.register("localhost:8082") == None)
	assert(await svr.select("name") == ["localhost:8082", 3])

	assert(await svr.unregister("localhost:8082") == True)
	assert(await svr.select("name") == ["localhost:8081", 2])

	assert(await svr.unregister("localhost:8081") == True)
	assert(await svr.select("name") == ["localhost:8080", 0])

	assert(await svr.unregister("localhost:8080") == True)

	assert(await svr.select("name") == [None, 0])

async def testServerLoadBalancer():
	from NameService import NameService
	name_service_address = startService(NameService)

	from interface.DBNode import DBNode
	db_address = startService(DBNode)

	from ServerLoadBalancer import ServerLoadBalancer
	ServerLoadBalancer.NameService = str(name_service_address)

	name_svr = ServerProxy("tcp://" + str(name_service_address)).NameService

	assert(await name_svr.register(str(db_address)) == None)

	local_address = startService(ServerLoadBalancer)

	svr = ServerProxy("tcp://" + str(local_address)).ServerLoadBalancer

	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("SET", "name", "cyk") == True)
	assert(await svr.forward("GET", "name") == "cyk")

	assert(await svr.forward("DELETE", "name") == 1)
	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("DELETE", "name") == 0)
	assert(await svr.forward("GET", "name") == None)

def main():
	asyncio.run(testDBNode())
	asyncio.run(testNameService())
	asyncio.run(testServerLoadBalancer())

if __name__ == "__main__":
	main()