#!python3

from multiprocessing import Process, Queue, freeze_support

freeze_support()
processQ = Queue()

import os
os.environ['PYTHONWARNINGS'] = 'ignore'

from nng_json_rpc.RPCClient import ServerProxy
import asyncio
import config

def check(ret):
	assert(ret)

async def testFull(port):
	local_address = "tcp://0.0.0.0:" + port
	svr = ServerProxy(local_address).ServerLoadBalancer

	async def execute(*args):
		print("start to execute: ", *args)
		ret = await svr.forward(*args)
		print("=> get result: ", ret)
		return ret

	assert(await execute("DELETE", "name") in [0, 1])

	assert(await execute("GET", "name") == None)

	assert(await execute("SET", "name", "COEN-317") == True)
	assert(await execute("GET", "name") == "COEN-317")

	assert(await execute("DELETE", "name") == 1)
	assert(await execute("GET", "name") == None)

	assert(await execute("DELETE", "name") == 0)
	assert(await execute("GET", "name") == None)

if __name__ == "__main__":
	import sys
	asyncio.run(testFull(sys.argv[1]))