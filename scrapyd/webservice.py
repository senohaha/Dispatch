# coding: utf-8
from copy import copy
import traceback

import uuid
from twisted.application.service import IServiceCollection
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from twisted.python import log

from .utils import JsonResource, native_stringify_dict
import redis
import json
import pymongo
import settingconfig
from random import choice

class WsResource(JsonResource):

    def __init__(self, root):
        JsonResource.__init__(self)
        self.root = root
        self.setting = settingconfig.SettingConfig()
        # 获取参数
        self.redis_host = self.setting.get('redis', 'redis_host')
        self.redis_port = self.setting.get('redis', 'redis_port')
        self.redis_pass = self.setting.get('redis', 'redis_pass')
        self.redis_conn = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_pass)

        self.mongo_host = self.setting.get('mongo', 'mongo_host')
        self.mongo_port = int(self.setting.get('mongo', 'mongo_port'))
        self.mongo_dbname = self.setting.get('mongo', 'mongo_dbname')
        self.mongo_username = self.setting.get('mongo', 'mongo_username')
        self.mongo_password = self.setting.get('mongo', 'mongo_password')
        if self.mongo_username == "":
            self.server = pymongo.MongoClient(host=self.mongo_host, port=self.mongo_port)
        else:
            self.server = pymongo.MongoClient('mongodb://{0}:{1}@{2}:{3}'.format(self.mongo_username,self.mongo_password,self.mongo_host,self.mongo_port))

        self.db = self.server[self.mongo_dbname]   # 库
        # self.db.authenticate(self.mongo_username, self.mongo_password, mechanism='SCRAM-SHA-1')

    def render(self, txrequest):
        try:
            return JsonResource.render(self, txrequest).encode('utf-8')
        except Exception as e:
            if self.root.debug:
                return traceback.format_exc().encode('utf-8')
            log.err()
            r = {"node_name": self.root.nodename, "status": "error", "message": str(e)}
            return self.render_object(r, txrequest).encode('utf-8')

class GetID(WsResource):        #  为物理机分配ID  ++

    def render_GET(self, txrequest):
        node_id = 1

        return {"slave_name": self.root.nodename, "status":"ok", "slave_id": node_id}

class HasProcess(WsResource):  # 判断一个用户的一个任务有哪些进程在爬
    def render_POST(self, txrequest):
        args = dict((k, v[0])for k, v in native_stringify_dict(copy(txrequest.args),keys_only=False).items())
        userId = args['userId']
        taskId = args['taskId']
        regex = 'process:*:{userId}:{taskId}:*'. \
            format(userId=userId, taskId=taskId)
        print regex,'77777777777777777777777&&&&&&&&&&&&&&&&&&&&&&&'
        res = []
        for key in self.redis_conn.scan_iter(match=regex):
            print key,'ppppppppppppppppppppbbbbbbbbbbbbbbbbbbbbbbbbbbb!!!!!!!!!!!!'
            res.append(key)
        return res

# 取代理ip
class GetProxy(WsResource):
    def render_POST(self, txrequest):
        """
                随机获取有效代理，首先尝试获取最高分数代理，如果不存在，按照排名获取，否则异常
                :return: 随机代理
                """
        result = self.db.zrangebyscore('proxypool', 100, 100)
        if len(result):
            proxy = choice(result)
        else:
            result = self.db.zrevrange('proxypool', 0, 100)
            if len(result):
                proxy = choice(result)   # 60.217.155.73:8060
            else:
                print '代理池为空'
                proxy = None

        return {"slave_name": self.root.nodename, "proxy": proxy}



class HasTask(WsResource):  # 爬虫管理器 判断所在物理机node_id是否有任务,并将该机器上所有任务返回 ++
    '''
    "node_id"
    return : [{signal:,userId:,taskId:}]
    '''

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        slaveID = args['slaveid'][0]
        # print slaveID
        regex = 'dispatch:{slaveId}:*:*:*'.format(slaveId=slaveID)
        res = []
        for key in self.redis_conn.scan_iter(match=regex):
            item = {}
            item['signal'] = self.redis_conn.get(key)
            item['userId'] = key.split(':')[2]
            item['taskId'] = key.split(':')[3]
            res.append(item)
            self.redis_conn.delete(key)
        return res

class StopTask(WsResource):     #  爬虫管理器 停止任务 +++
    '''
    "slaveId": self.slave_id,
    "userId": userId,
    "taskId": taskId,
    "pid": pid
    '''
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        slaveID = args['slaveId']
        userId = args['userId']
        taskId = args['taskId']
        pid = args['pid']
        processLiveKey = 'process:{slaveId}:{userId}:{taskId}:{pid}'. \
            format(slaveId=slaveID, userId=userId, taskId=taskId, pid=pid)
        self.redis_conn.set(processLiveKey, 'stop')
        return {"slave_name": self.root.nodename, "status": "ok"}

class NodeInfo(WsResource):  # 爬虫管理器 定时汇报所在节点信息
    """
    "slave_id"
    "node_info"
    """
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        # 待完善！




class LockInsertRedis(WsResource):    # 爬从 同步锁 向redis数据库插入数据（task:userId:taskId:desc）中的dataCount,repeatCount
    """
    :param key:
    :param flag_repeatCount: 是否对该字段加1，true加1
    :return:
    """
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        flag_repeatCount_str = args['flag_repeatCount']
        print flag_repeatCount_str, 'Dispatch!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!flag_repeatCount_str@@@@@@@@@@@'
        if flag_repeatCount_str == 'False':
            flag_repeatCount = False
        else:
            flag_repeatCount = True
        print flag_repeatCount, 'Dispatch!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'


        with self.redis_conn.pipeline() as pipe:
            while 1:
                try:
                    pipe.watch(key)
                    dataCount = pipe.hget(key, 'dataCount')
                    if dataCount is None:
                        dataCount=0
                    dataCount = int(dataCount) + 1
                    if flag_repeatCount is True:
                        repeatCount = pipe.hget(key, 'repeatCount')
                        if repeatCount is None:
                            repeatCount = 0

                    pipe.multi()
                    if flag_repeatCount is True:
                        pipe.hset(key, 'repeatCount', int(repeatCount) + 1)
                    pipe.hset(key, 'dataCount', dataCount)
                    pipe.execute()
                    break
                except WatchError:
                    continue
                except Exception:
                    print 'redis 操作异常'
                    break


class MongoFindOne(WsResource):          # 爬虫判断mongo里是否有重复数据
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        userId = args['userId']
        taskId = args['taskId']
        item = args['item']
        item = json.loads(item)
        collection = 'user_{userId}_{taskId}'.format(userId=userId, taskId=taskId)
        # self.db.authenticate(self.mongo_username, self.mongo_password, mechanism='SCRAM-SHA-1')
        coll = self.db[collection]  # 集合
        if coll.find_one(item) is None:
            res = True   # 该数据不存在
        else:
            res = False
        print res, '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        return {"slave_name": self.root.nodename, "find_one": res }


class MongoInsert(WsResource):    # 爬虫  插入mongodb数据
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        userId = args['userId']
        taskId = args['taskId']
        item = args['item']
        item = json.loads(item)
        collection = 'user_{userId}_{taskId}'.format(userId=userId, taskId=taskId)
        self.coll = self.db[collection]  # 集合
        self.coll.insert(item)
        return {"slave_name": self.root.nodename, "status": "ok"}

class GetTask(WsResource):      #  爬虫获取任务的接口
    def render_POST(self, txrequest):
        pass

class RedisLlen(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        key = args['key']
        len = self.redis_conn.llen(key)
        return {"slave_name": self.root.nodename, "len": len}

class RedisHset(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        field = args['field']
        value = args['value']
        self.redis_conn.hset(key, field, value)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisSet(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        value = args['value']
        self.redis_conn.set(key, value)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisLpush(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        value = args['value']
        self.redis_conn.lpush(key, value)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisExpire(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        time = args['time']
        self.redis_conn.expire(key, time)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisDelete(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        self.redis_conn.delete(key)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisLrem(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        key = args['key']
        value = args['value']
        num = args['num']
        self.redis_conn.lrem(key, num, value)
        return {"slave_name": self.root.nodename, "status": "ok"}

class RedisHget(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        key = args['key']
        field = args['field']
        value = self.redis_conn.hget(key, field)
        return {"slave_name": self.root.nodename, "value": value}

class RedisGet(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        key = args['key']
        value = self.redis_conn.get(key)
        return {"slave_name": self.root.nodename, "value": value}

class RedisLpop(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        key = args['key']
        value = self.redis_conn.lpop(key)
        return {"slave_name": self.root.nodename, "value": value}


# 判断一个用户下的所有任务 runningNode 和 MaxNode
class ComRunAndMax(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                  keys_only=False).items())
        userId = args['userId']
        ScheKey = 'scheduler:{userId}'.format(userId=userId)
        maxNode = self.redis_conn.hget(ScheKey, 'maxNode')

        sum_runningNode = 0
        TaskDescKey = 'task:{userId}:*:desc'.format(userId=userId)
        for key in self.redis_conn.scan_iter(match=TaskDescKey):
            runningNode = int(self.redis_conn.hget(key, 'runningNode'))
            sum_runningNode += runningNode

        if sum_runningNode < maxNode:  # 说明该用户下所有任务正在运行的节点个数《该用户拥有的节点个数，可启动
            return {"slave_name": self.root.nodename, "value": True}
        else:
            return {"slave_name": self.root.nodename, "value": False}


#  在一个任务启动或停止时，更新某个任务的runningNode的配置
class ChangeRunningNode(WsResource):
    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        userId = args['userId']
        taskId = args['taskId']
        status = int(args['status'])    # 0 为--    1为++
        TaskDescKey = 'task:{userId}:{taskId}:desc'.format(userId=userId, taskId=taskId)
        runningNode = int(self.redis_conn.hget(TaskDescKey, 'runningNode'))
        if status == 0:
            self.redis_conn.hset(TaskDescKey, 'runningNode', runningNode-1)
        elif status == 1:
            self.redis_conn.hset(TaskDescKey, 'runningNode', runningNode+1)
        return {"slave_name": self.root.nodename, "status": "ok"}


class Schedule(WsResource):

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        settings = args.pop('setting', [])
        settings = dict(x.split('=', 1) for x in settings)
        print settings
        item = args['item']
        print item
        import json
        print json.loads(item[0])
        # project = args.pop('project')
        # spider = args.pop('spider')
        # version = args.get('_version', '')
        # spiders = get_spider_list(project, version=version)
        # if not spider in spiders:
        #     return {"status": "error", "message": "spider '%s' not found" % spider}
        # args['settings'] = settings
        # jobid = args.pop('jobid', uuid.uuid1().hex)
        #
        # args['_job'] = jobid
        # self.root.scheduler.schedule(project, spider, **args)

        # args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        #
        # args = dict((k, v[0]) for k, v in args.items())
        # crawlid = args.pop('crawlid')
        # appid = args.pop('appid')
        #
        # app = IServiceCollection(self.root.app, self.root.app)
        # self.launcher = app.getServiceNamed('launcher')
        # self.root.launcher._spawn_process(appid, crawlid)


        return {"node_name": self.root.nodename, "status": "ok"}


class Cancel(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                    keys_only=False).items())
        print args,'hahaha'
        project = args['project']
        jobid = args['job']
        signal = args.get('signal', 'TERM')
        # prevstate = None
        # queue = self.root.poller.queues[project]
        # c = queue.remove(lambda x: x["_job"] == jobid)
        # if c:
        #     prevstate = "pending"
        # spiders = self.root.launcher.processes.values()
        # for s in spiders:
        #     if s.job == jobid:
        #         s.transport.signalProcess(signal)
        #         prevstate = "running"
        return {"node_name": self.root.nodename, "status": "ok",}

class AddVersion(WsResource):

    def render_POST(self, txrequest):
        project = txrequest.args[b'project'][0].decode('utf-8')
        version = txrequest.args[b'version'][0].decode('utf-8')
        eggf = BytesIO(txrequest.args[b'egg'][0])
        self.root.eggstorage.put(eggf, project, version)
        spiders = get_spider_list(project, version=version)
        self.root.update_projects()
        UtilsCache.invalid_cache(project)
        return {"node_name": self.root.nodename, "status": "ok", "project": project, "version": version, \
            "spiders": len(spiders)}

class ListProjects(WsResource):

    def render_GET(self, txrequest):
        projects = list(self.root.scheduler.list_projects())
        return {"node_name": self.root.nodename, "status": "ok", "projects": projects}



class ListSpiders(WsResource):

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        version = args.get('_version', [''])[0]
        spiders = get_spider_list(project, runner=self.root.runner, version=version)
        return {"node_name": self.root.nodename, "status": "ok", "spiders": spiders}

class ListJobs(WsResource):

    def render_GET(self, txrequest):
        # print 'listjobLLLLLLLLLLLLLLLLLLLLLLL:', txrequest
        # print txrequest.args
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args.get('project', [None])[0]
        spiders = self.root.launcher.processes.values()
        queues = self.root.poller.queues
        pending = [
            {"project": project, "spider": x["name"], "id": x["_job"]}
            for qname in (queues if project is None else [project])
            for x in queues[qname].list()
        ]
        running = [
            {
                "project": project,
                "spider": s.spider,
                "id": s.job, "pid": s.pid,
                "start_time": str(s.start_time),
            } for s in spiders if project is None or s.project == project
        ]
        finished = [
            {
                "project": project,
                "spider": s.spider, "id": s.job,
                "start_time": str(s.start_time),
                "end_time": str(s.end_time)
            } for s in self.root.launcher.finished
            if project is None or s.project == project
        ]
        return {"node_name": self.root.nodename, "status": "ok",
                "pending": pending, "running": running, "finished": finished}

class DeleteProject(WsResource):

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        self._delete_version(project)
        UtilsCache.invalid_cache(project)
        return {"node_name": self.root.nodename, "status": "ok"}

    def _delete_version(self, project, version=None):
        self.root.eggstorage.delete(project, version)
        self.root.update_projects()

class DeleteVersion(DeleteProject):

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        version = args['version'][0]
        self._delete_version(project, version)
        UtilsCache.invalid_cache(project)
        return {"node_name": self.root.nodename, "status": "ok"}
