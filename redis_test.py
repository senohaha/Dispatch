# -*- coding: utf-8 -*-

import redis
import uuid
import datetime
import random
from collections import OrderedDict
import json
# r = redis.StrictRedis(host='192.168.20.115', port=6379, password='jzspider')
# redis_conn = redis.StrictRedis(host='192.168.20.111', port=6379)
# redis_conn.scan()
# test1

# 用户8的配置
# map = {'maxNode': 10, 'maxRunTask': 4, 'runningTask': 0, 'flag': 1}
# print redis_conn.hmset('scheduler:8', map)
# # 用户8 目前有一个任务1,2待运行
# map_desc = {'taskMaxNode': 0, 'runningNode': 0, 'status': 0, 'taskDescription': 'papapapapa', 'startTimeStamp':0,'endTimeStamp':0}
# redis_conn.hmset('task:8:1:desc', mapping=map_desc)
# map_desc = {'taskMaxNode': 0, 'runningNode': 0, 'status': 0, 'taskDescription': 'papapapapa', 'startTimeStamp':0,'endTimeStamp':0}
# redis_conn.hmset('task:8:2:desc', mapping=map_desc)


# map1 = {'maxNode':10,'maxRunTask':3,'runingTask':0,'flag':1}
# map2 = {'maxNode':11,'maxRunTask':3,'runingTask':0,'flag':1}
# map3 = {'maxNode':12,'maxRunTask':3,'runingTask':0,'flag':1}
# print redis_conn.hmset('scheduler:9',map1)
# print redis_conn.hmset('scheduler:10',map2)
# print redis_conn.hmset('scheduler:11',map)



#
# print r.hget('')
# a = r.hget('task:8:7','taskDescription')
# # print a
# dictdata = json.loads(a, object_pairs_hook=OrderedDict)
#
# print dictdata['task']['opList']
#
# map1 = {'taskMaxNode':'0','status':'0'}
# map2 = {'taskMaxNode':'10','status':'1'}
# map3 = {'taskMaxNode':'0','status':'0'}
# map4 = {'taskMaxNode':'0','status':'0'}
# map5 = {'taskMaxNode':'0','status':'0'}
# map6 = {'taskMaxNode':'0','status':'0'}
# map7 = {'taskMaxNode':'0','status':'3'}
# map8 = {'taskMaxNode':'0','status':'4'}
# redis_conn.hmset('task:11:1', map1)
# redis_conn.hmset('task:11:2', map2)
# redis_conn.hmset('task:11:3', map3)
# redis_conn.hmset('task:11:4', map4)
# redis_conn.hmset('task:11:5', map5)
# redis_conn.hmset('task:11:6', map6)
# redis_conn.hmset('task:11:7', map7)
# redis_conn.hmset('task:11:8', map8)
# redis_conn.hset('task:11:3', 'status',4)
# redis_conn.hset('task:11:3', 'taskMaxNode',0)

# for key in redis_conn.scan_iter(match='task:11*'):
#     print key
#     print 'taskMaxNode:',redis_conn.hget(key,'taskMaxNode')
#     print 'status:',redis_conn.hget(key,'status')
#     print '***************'
#
# print redis_conn.hgetall('scheduler:11')
# redis_conn.lpush("task:11:1:urlList","aaa")
import urllib2
# Redis_Host = None
# Redis_Port = None
# Redis_Pass = None
# Redis_Cluster = None
#
# Mongo_Host = None
# Mongo_Port = None
# Mongo_Username = None
# Mongo_Dbname = None
# Mongo_Password = None
# Mongo_Cluster = None




# global Redis_Host
# global Redis_Port
# global Redis_Pass
# global Redis_Cluster
#
# global Mongo_Host
# global Mongo_Port
# global Mongo_Username
# global Mongo_Dbname
# global Mongo_Password
# global Mongo_Cluster
LL = 'sss'

def get_setting(domain):
    url = 'http://{domain}/api/admin/config/node_get'.format(domain=domain)
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    setting = res.read()
    json_set = json.loads(setting)
    redisConfig = json_set['body']['redisConfig']
    mongoConfig = json_set['body']['mongoConfig']
    dispatcherConfig = json_set['body']['dispatcherConfig']


    Redis_Host = redisConfig['host']
    Redis_Cluster = redisConfig['cluster']
    Redis_Pass = redisConfig['password']
    Redis_Port = redisConfig['port']

    Mongo_Host = mongoConfig['host']
    Mongo_Port = mongoConfig['port']
    Mongo_Username = mongoConfig['username']
    Mongo_Dbname = mongoConfig['dbname']
    Mongo_Password = mongoConfig['password']
    Mongo_Cluster = mongoConfig['cluster']




if __name__ == '__main__':
    get_setting('192.168.20.109:8080/jzSpiderCMS')