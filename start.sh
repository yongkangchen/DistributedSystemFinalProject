nohup python main.py NameService >> NameService.log 2>&1 &
nohup python main.py DBNode >> DBNode.log 2>&1 &
nohup python main.py CacheNode >> CacheNode.log 2>&1 &
nohup python main.py ServerLoadBalancer >> ServerLoadBalancer.log 2>&1 &