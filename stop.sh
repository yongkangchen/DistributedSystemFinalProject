kill `lsof NameService.log | grep 1w | awk '{print $2}'`
kill `lsof DBNode.log | grep 1w | awk '{print $2}'`
kill `lsof CacheNode.log | grep 1w | awk '{print $2}'`
kill `lsof ServerLoadBalancer.log | grep 1w | awk '{print $2}'`