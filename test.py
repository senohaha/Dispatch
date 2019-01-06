# coding=utf-8

import random,string
import hashlib
import requests
import json
import ConfigParser
def genRandomString(slen=16):
    return ''.join(random.sample(string.ascii_letters + string.digits, slen))
rand = genRandomString()
print 'rand=', rand
str = "appId=3003716925983325&nonce_str={random}&type=1&key=fnVigs15iwgwBYJxkaNCCGT8NtMzykwG".format(random = rand)
print 'str=', str
m = hashlib.md5()  # 创建md5对象
m.update(str.encode())  # 生成加密串
result = m.hexdigest()  # 打印经过md5加密的字符串
result = result.upper()
print result
response = requests.post('http://183.223.236.38:19090/jzSpiderCMS/api/admin/config/dispatch_url.jspx',data={'nonce_str':rand,'appId':'3003716925983325','sign':result,'type':1})
# response = requests.get('http://183.223.236.38:19090/jzSpiderCMS/api/admin/config/node_get.jspx?appId=3003716925983325&nonce_str={a}&sign={b}'.format(a=rand,b=result))
setting = response.text
if response.status_code == 200:
    print
print setting
json_set = json.loads(setting)
# redisConfig = json_set['body']['redisConfig']
# mongoConfig = json_set['body']['mongoConfig']
dispatcherConfig = json_set['body']['dispatcherConfig']



# Redis_Host = redisConfig['host']
# Redis_Cluster = redisConfig['cluster']
# Redis_Pass = redisConfig['password']
# Redis_Port = redisConfig['port']
#
# Mongo_Host = mongoConfig['host']
# Mongo_Port = mongoConfig['port']
# Mongo_Username = mongoConfig['username']
# Mongo_Dbname = mongoConfig['dbname']
# Mongo_Password = mongoConfig['password']
# Mongo_Cluster = mongoConfig['cluster']


fp = 'dfydfysetting.conf'
conf = ConfigParser.ConfigParser()
# conf.add_section('redis')
# conf.set('redis', 'redis_host', Redis_Host)
# conf.set('redis', 'redis_cluster', Redis_Cluster)
# conf.set('redis', 'redis_pass', Redis_Pass)
# conf.set('redis', 'redis_port', Redis_Port)
conf.add_section('mongo')
# conf.set('mongo', 'mongo_host', Mongo_Host)
# conf.set('mongo', 'mongo_port', Mongo_Port)
# conf.set('mongo', 'mongo_username', Mongo_Username)
# conf.set('mongo', 'mongo_dbname', Mongo_Dbname)
# conf.set('mongo', 'mongo_password', Mongo_Password)
conf.set('mongo', 'dispatcherConfig', dispatcherConfig)

with open(fp, 'w') as fw:
    conf.write(fw)
