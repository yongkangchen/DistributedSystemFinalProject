import pynng
import asyncio

from jsonrpc import JSONRPCResponseManager, Dispatcher

class RPCServer:
	def __init__(self, address):
		self.address = address
		self.dispatcher = Dispatcher()
		
		self.ssock = pynng.Rep0()
		lis = self.ssock.listen(self.address)
		
		self.local_address = lis.local_address

	def register_function(self, function = None, name = None):
		return self.dispatcher.add_method(function, name)

	def build_method_map(self, prototype, prefix=''):
		return self.dispatcher.build_method_map(prototype, prefix)

	async def response(self, sock, msg):
		content = msg.bytes.decode()

		# print("request content: ", content)
		
		response = JSONRPCResponseManager.handle(
			content, self.dispatcher)

		if response is None: 
			# print("response content => ", None)
			return

		if asyncio.iscoroutine(response.result) or asyncio.isfuture(response.result):
			response.result = await response.result
		
		# print("response content => ", response.json)
		await sock.asend(response.json.encode())

	async def start(self):
		while True:
			sock = self.ssock.new_context()
			
			msg = await sock.arecv_msg()

			asyncio.create_task(self.response(sock, msg))

	def serve_forever(self):
		asyncio.run(self.start())

if __name__ == "__main__":
	server = RPCServer("tcp://0.0.0.0:8080")

	import datetime
	# @server.register_function
	def today():
		ret = datetime.datetime.today().ctime()
		print("call today: ", ret)
		return ret

	server.register_function(today, "today")
	server.serve_forever()
