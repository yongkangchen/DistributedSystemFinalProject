from nng_json_rpc.RPCClient import ServerProxy

class RPCFactory:
	cache = {}
	def getInstance(name):
		cache = RPCFactory.cache
		if name in cache: return cache[name]
		proxy = ServerProxy(name)
		cache[name] = proxy
		return proxy

