import pynng
import json
from functools import cache
from functools import partialmethod

JSONRPC_VERSION = "2.0"

class Fault(Exception):
	"""Indicates an XML-RPC fault package."""
	def __init__(self, faultCode, faultString, **extra):
		Exception.__init__(self)
		self.faultCode = faultCode
		self.faultString = faultString
	def __repr__(self):
		return "<%s %s: %r>" % (self.__class__.__name__,
								self.faultCode, self.faultString)
class _Method:
	def __init__(self, send, name):
		self.__send = send
		self.__name = name
		
	def __getattr__(self, name):
		return _Method(self.__send, "%s.%s" % (self.__name, name))
	def __call__(self, *args):
		return self.__send(self.__name, args)

class _Notify:
	def __init__(self, send):
		self.__send = send
	def __getattr__(self, name):
		return _Method(self.__send, name)

class ServerProxy:
	def __init__(self, address):
		self.sock = None
		self.address = address
		self.id = 0
		self.notify = _Notify(self.__notify)

	async def __notify(self, methodname, params):
		return await self.__send(True, methodname, params)

	async def __request(self, methodname, params):
		return await self.__send(False, methodname, params, )

	async def __send(self, is_notify, methodname, params):
		if self.sock is None:
			self.sock = pynng.Req0()
			self.sock.dial(self.address)

		msg = {"jsonrpc": JSONRPC_VERSION, "method": methodname, "params": params}

		if not is_notify: 
			msg["id"] = self.id
			self.id += 1

		await self.sock.asend(json.dumps(msg).encode())
		
		if is_notify: return

		msg = await self.sock.arecv_msg()
		msg = msg.bytes.decode()

		response = json.loads(msg)

		if "error" in response:
			error = response["error"]
			raise Fault(error["code"], error["message"])

		return response["result"]

	@cache
	def __getattr__(self, name):
		return _Method(self.__request, name)

if __name__ == "__main__":
	import asyncio

	async def main():
		print(await ServerProxy("tcp://127.0.0.1:8080").notify.today())

		svr = ServerProxy("tcp://127.0.0.1:8080")
		print(await svr.today())
		
		await asyncio.sleep(1)
		
		print(await svr.notify.today())
		

	asyncio.run(main())
