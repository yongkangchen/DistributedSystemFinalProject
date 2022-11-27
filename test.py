#!python3

from multiprocessing import Process, Queue, freeze_support

freeze_support()
processQ = Queue()

import os
os.environ['PYTHONWARNINGS'] = 'ignore'

from nng_json_rpc.RPCClient import ServerProxy
import asyncio

def runInProcess(q, serviceName):
	from importlib import import_module

	from nng_json_rpc.RPCServer import RPCServer
	server = RPCServer("tcp://127.0.0.1:0")

	q.put("tcp://" + str(server.local_address))

	service = getattr(import_module(serviceName), serviceName.split(".").pop())
	
	if getattr(service, "init", None):
		service.init()

	server.build_method_map(service, service.__name__ + ".")
	server.build_method_map(service)

	server.serve_forever()

def startService(serviceName):
	global processQ

	p = Process(target = runInProcess, args = [processQ, serviceName])
	p.start()

	return processQ.get(), p

async def testInterfaceDBNode():
	local_address, childProcess = startService("interface.DBNode")

	svr = ServerProxy(local_address).DBNode
		
	assert(await svr.command("GET", "name", 0) == None)
	

	assert(await svr.command("SET", "name", 0, "cyk") == True)
	assert(await svr.command("GET", "name", 0) == "cyk")

	assert(await svr.command("DELETE", "name", 0) == 1)
	assert(await svr.command("GET", "name", 0) == None)

	assert(await svr.command("DELETE", "name", 0) == 0)

	childProcess.kill()

async def testDBNode():
	local_address, childProcess = startService("DBNode")

	svr = ServerProxy(local_address).DBNode

	assert(await svr.command("DELETE", "name", 0) in [0,1])

	assert(await svr.command("GET", "name", 0) == None)


	assert(await svr.command("SET", "name", 0, "cyk") == True)

	assert(await svr.command("GET", "name", 0) == "cyk")

	assert(await svr.command("DELETE", "name", 0) == 1)
	assert(await svr.command("GET", "name", 0) == None)

	assert(await svr.command("DELETE", "name", 0) == 0)


	childProcess.kill()
	

async def testNameService():
	local_address, childProcess = startService("NameService")

	svr = ServerProxy(local_address).NameService

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

	childProcess.kill()

async def testServerLoadBalancer():
	name_service_address, nameProcess = startService("NameService")

	db_address, dbProcess = startService("interface.DBNode")

	name_svr = ServerProxy(name_service_address).NameService

	assert(await name_svr.register(db_address) == None)

	local_address, slbProcess = startService("ServerLoadBalancer")

	svr = ServerProxy(local_address).ServerLoadBalancer

	assert(await svr.bind(name_service_address) == True)

	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("SET", "name", "cyk") == True)
	assert(await svr.forward("GET", "name") == "cyk")

	assert(await svr.forward("DELETE", "name") == 1)
	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("DELETE", "name") == 0)
	assert(await svr.forward("GET", "name") == None)

	nameProcess.kill()
	dbProcess.kill()
	slbProcess.kill()

async def testCache():
	name_service_address, nameProcess = startService("NameService")

	db_address, dbProcess = startService("interface.DBNode")

	cache_address, cacheProcess = startService("CacheNode")

	name_svr = ServerProxy(name_service_address).NameService

	assert(await name_svr.register(str(db_address)) == None)

	db_svr = ServerProxy(db_address).DBNode

	cache_svr = ServerProxy(cache_address).CacheNode

	assert(await cache_svr.set_up(db_address, name_service_address, cache_address, 30) == True)

	assert(await cache_svr.command("GET", "name", 0) == None)
	
	assert(await cache_svr.command("SET", "name", 0, "cyk") == True)
	assert(await cache_svr.command("GET", "name", 0) == "cyk")

	assert(await cache_svr.command("DELETE", "name", 0) == 1)
	assert(await cache_svr.command("GET", "name", 0) == None)

	assert(await cache_svr.command("DELETE", "name", 0) == 0)
	
	nameProcess.kill()
	dbProcess.kill()
	cacheProcess.kill()

async def testFull():
	name_service_address, nameProcess = startService("NameService")
	cache_address, cacheProcess = startService("CacheNode")

	name_svr = ServerProxy(name_service_address).NameService
	assert(await name_svr.register(cache_address) == None)

	db_address, dbProcess = startService("DBNode")
	cache_svr = ServerProxy(cache_address).CacheNode
	assert(await cache_svr.set_up(db_address, name_service_address, cache_address, 30) == True)

	local_address, slbProcess = startService("ServerLoadBalancer")
	svr = ServerProxy(local_address).ServerLoadBalancer

	assert(await svr.bind(name_service_address) == True)

	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("SET", "name", "cyk") == True)
	assert(await svr.forward("GET", "name") == "cyk")

	assert(await svr.forward("DELETE", "name") == 1)
	assert(await svr.forward("GET", "name") == None)

	assert(await svr.forward("DELETE", "name") == 0)
	assert(await svr.forward("GET", "name") == None)
	
	nameProcess.kill()
	dbProcess.kill()
	cacheProcess.kill()
	slbProcess.kill()

async def sleepWithLog(sec):
	print("going to sleep: %d seconds" % sec)
	for i in range(sec):
		print("sleep: ", sec - i)
		await asyncio.sleep(1)

async def testHeartbeat():
	name_service_address, nameProcess = startService("NameService")
	cache_address, cacheProcess = startService("CacheNode")

	name_svr = ServerProxy(name_service_address).NameService
	cache_svr = ServerProxy(cache_address).CacheNode

	assert(await name_svr.register(cache_address) == None)

	assert(await name_svr.start_check_all_heartbeat() == None)
	await sleepWithLog(10)

	assert(cache_address in await name_svr.get_alive_node_dict())

	cacheProcess.kill()
	await sleepWithLog(10)

	assert(cache_address not in await name_svr.get_alive_node_dict())   # check if a node is down

	cache_address, cacheProcess = startService("CacheNode")
	cache_svr = ServerProxy(cache_address).CacheNode
	assert(await name_svr.register(cache_address) == None)
	await sleepWithLog(12)

	print(cache_address, await name_svr.get_alive_node_dict())
	assert(cache_address in await name_svr.get_alive_node_dict())    # check if a node is recovered

	cacheProcess.kill()
	nameProcess.kill()

def main():
	asyncio.run(testInterfaceDBNode())
	asyncio.run(testDBNode())
	asyncio.run(testNameService())
	asyncio.run(testServerLoadBalancer())
	asyncio.run(testCache())
	asyncio.run(testHeartbeat())
	asyncio.run(testFull())

if __name__ == "__main__":
	main()