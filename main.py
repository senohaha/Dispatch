# coding=utf-8
#!/usr/bin/env python

from twisted.scripts.twistd import run
from os.path import join, dirname
from sys import argv
import sys
import scrapyd
import urllib2
import json
import random, string
import hashlib
import requests
import ConfigParser


def genRandomString(slen=16):
    return ''.join(random.sample(string.ascii_letters + string.digits, slen))
# http://39.105.42.151:8080/jzSpiderCMS/api/admin/config/node_get
# http://192.168.20.111:8080/jzSpiderCMS/api/admin/config/node_get
def get_setting(domain,appId='3003716925983325',key='fnVigs15iwgwBYJxkaNCCGT8NtMzykwG'):
    url = '{domain}/api/admin/config/node_get.jspx'.format(domain=domain)
    print url
    rand = genRandomString()
    str = "appId={appId}&nonce_str={random}&key={key}".format(random=rand,appId=appId,key=key)
    m = hashlib.md5()  # 创建md5对象
    m.update(str.encode())  # 生成加密串
    result = m.hexdigest()  # 打印经过md5加密的字符串
    result = result.upper()
    # response = requests.post(url,data={'nonce_str': rand, 'appId': appId, 'sign': result})
    response = requests.get('http://10.195.112.11:9090/jzSpiderCMS/api/admin/config/node_get.jspx?appId=3003716925983325&nonce_str={a}&sign={b}'.format(a=rand,b=result))
    if response.status_code !=200:
        print response.text
        return
    setting = response.text
    print setting, 'dddddd !!!!!!'
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


    fp = 'setting.conf'
    conf = ConfigParser.ConfigParser()
    conf.add_section('redis')
    conf.set('redis', 'redis_host', Redis_Host)
    conf.set('redis', 'redis_cluster', Redis_Cluster)
    conf.set('redis', 'redis_pass', Redis_Pass)
    conf.set('redis', 'redis_port', Redis_Port)
    conf.add_section('mongo')
    conf.set('mongo', 'mongo_host', Mongo_Host)
    conf.set('mongo', 'mongo_port', Mongo_Port)
    conf.set('mongo', 'mongo_username', Mongo_Username)
    conf.set('mongo', 'mongo_dbname', Mongo_Dbname)
    conf.set('mongo', 'mongo_password', Mongo_Password)
    conf.set('mongo', 'mongo_cluster', Mongo_Cluster)

    with open(fp, 'w') as fw:
        conf.write(fw)

def createSign():
    pass

def main():
    argv[1:] = ['-n', '-y', join(dirname(scrapyd.__file__), 'txapp.py')]
    run()

if __name__ == '__main__':
    # domian = sys.argv[1]
    # print domian
    get_setting(domain='http://183.223.236.38:19090/jzSpiderCMS')
    main()

