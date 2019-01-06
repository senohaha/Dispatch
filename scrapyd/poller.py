# -*- coding: utf-8 -*-
import redis_lock
from zope.interface import implementer

from .interfaces import IPoller

import fcntl
import struct
import uuid
import redis
import socket
import datetime
import settingconfig

import random
REDIS_LOCK_EXPIRATION = 6


#  轮询用户配置并进行调度
@implementer(IPoller)
class QueuePoller(object):

    def __init__(self, config, app):
        self.app = app
        self.setting = settingconfig.SettingConfig()
        # 获取参数
        self.redis_host = self.setting.get('redis', 'redis_host')
        self.redis_port = self.setting.get('redis', 'redis_port')
        self.redis_pass = self.setting.get('redis', 'redis_pass')
        # print self.redis_host, self.redis_port, self.redis_pass, '-----------------!!!!!1'
        self.redis_conn = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_pass)

    def poll(self):
        regex = 'scheduler:*'
        for key in self.redis_conn.scan_iter(match=regex):
            # acquire lock
            lock = self._create_lock_object(key)
            try:
                if lock.acquire(blocking=False):   # 若有其他进程在操作该key，则跳过对该key的处理
                    val = int(self.redis_conn.hget(key, 'flag'))
                    userId = key.split(":")[1]
                    userTaskKey = 'task:{userId}:*:desc'.format(userId=userId)
                    maxNode = int(self.redis_conn.hget(key, 'maxNode'))
                    maxRunTask = int(self.redis_conn.hget(key, 'maxRunTask'))
                    runningTask = int(self.redis_conn.hget(key, 'runningTask'))

                    if val == 1:   # 若该用户配置改变，或者 存在等待的 并且 运行的任务个数小于用户设置的并行的任务数
                        runningTaskids = self._get_running_task(userTaskKey)
                        waitTaskids = self._get_wait_task(userTaskKey)
                        taskNum = len(runningTaskids)+len(waitTaskids)     # 用户 待运行 以及 正在运行 总任务数

                        realMaxRunTask = maxRunTask if maxRunTask < taskNum else taskNum


                        if realMaxRunTask == 0:
                            realMaxRunTask=1

                        base = maxNode / realMaxRunTask
                        mod = maxNode % realMaxRunTask
                        taskMaxNode = [base+1 if i < mod else base for i in range(realMaxRunTask)]

                        if len(runningTaskids) < realMaxRunTask:   # 如果正在运行的任务个数<分配的最大运行任务数,运行的减少节点，并启动新的任务
                            addRunTask = realMaxRunTask-len(runningTaskids)
                            add_id = 0
                            taskMaxNode_id = 0
                            for taskid in runningTaskids:
                                taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId,taskid=taskid[1])
                                self.redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                                taskMaxNode_id += 1
                            for taskid in waitTaskids:
                                if add_id >= addRunTask:
                                    break
                                taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                                self.redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                                self.redis_conn.hset(taskkey, 'status', 1)
                                add_id += 1
                                taskMaxNode_id += 1
                        else:   # 将部分运行任务变为等待状态（停止最晚启动的任务！！！！！！），部分运行的任务增加节点
                            real_id = 0
                            taskMaxNode_id = 0
                            for taskid in runningTaskids:
                                taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid[1])
                                if real_id < realMaxRunTask:
                                    self.redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                                    taskMaxNode_id += 1
                                    real_id += 1
                                else:
                                    self.redis_conn.hset(taskkey, 'taskMaxNode', 0)
                                    self.redis_conn.hset(taskkey, 'status', 0)
                        self.redis_conn.hset(key, 'runningTask', realMaxRunTask)
                        self.redis_conn.hset(key, 'flag', '0')

                    elif len(self._get_running_task(userTaskKey)) < maxRunTask \
                            and len(self._get_wait_task(userTaskKey)) != 0:
                        # 存在等待的 并且 运行的任务个数小于用户设置的并行的任务数
                        # 从运行的任务 匀出 部分进程  。 从等待的执行的任务中选出部分启动(将状态变为运行)
                        runningTaskids = self._get_running_task(userTaskKey)
                        waitTaskids = self._get_wait_task(userTaskKey)
                        taskNum = len(runningTaskids) + len(waitTaskids)
                        realMaxRunTask = maxRunTask if maxRunTask < taskNum else taskNum

                        if realMaxRunTask == 0:
                            realMaxRunTask = 1

                        base = maxNode / realMaxRunTask
                        mod = maxNode % realMaxRunTask
                        taskMaxNode = [base + 1 if i < mod else base for i in range(realMaxRunTask)]

                        addRunTask = realMaxRunTask - len(runningTaskids)
                        add_id = 0
                        taskMaxNode_id = 0
                        for taskid in runningTaskids:
                            taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid[1])
                            self.redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                            taskMaxNode_id += 1
                        #  使用callback函数，当运行的任务所分配的线程减少到指定线程后，再启动等待的任务。！！！！！！
                        for taskid in waitTaskids:
                            if add_id >= addRunTask:
                                break
                            taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                            self.redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                            self.redis_conn.hset(taskkey, 'status', 1)
                            add_id += 1
                            taskMaxNode_id += 1
                        self.redis_conn.hset(key, 'runningTask', realMaxRunTask)

            except Exception:
                # self.logger.error(traceback.format_exc())
                # self._increment_fail_stat('{k}:{v}'.format(k=key, v=val))
                #
                # self._process_failures(key)
                print 'redis Exception1'

            # remove lock regardless of if exception or was handled ok
            if lock._held:
                print "releasing1 lock"
                lock.release()

    def _get_wait_task(self, userTaskKey):
        waitTaskids = []
        for userTask in self.redis_conn.scan_iter(match=userTaskKey):
            taskid = userTask.split(':')[2]
            if self.redis_conn.hget(userTask, 'status') == '0':
                waitTaskids.append(taskid)
        return waitTaskids

    # 获取正在运行的任务id及其启动时间，[(startTime, taskId),(...),(...)]并返回排好序的list
    def _get_running_task(self, userTaskKey):
        runningTaskids = []
        for userTask in self.redis_conn.scan_iter(match=userTaskKey):
            taskid = userTask.split(':')[2]
            if self.redis_conn.hget(userTask, 'status') == '1':
                startTime = str(self.redis_conn.hget(userTask, 'startTimeStamp'))
                tup_temp = (startTime, taskid)
                runningTaskids.append(tup_temp)
        return sorted(runningTaskids)

    def _create_lock_object(self, key):
        '''
        Returns a lock object, split for testing
        '''
        return redis_lock.Lock(self.redis_conn, key,
                               expire=REDIS_LOCK_EXPIRATION,
                               auto_renewal=True)
    def next(self):
        pass


    # def update_projects(self):
    #     pass


# 轮询用户任务并进行调度
@implementer(IPoller)
class TaskPoller(object):

    def __init__(self, config, app):
        self.app = app
        self.setting = settingconfig.SettingConfig()
        # 获取参数
        self.redis_host = self.setting.get('redis', 'redis_host')
        self.redis_port = self.setting.get('redis', 'redis_port')
        self.redis_pass = self.setting.get('redis', 'redis_pass')
        print self.redis_host, self.redis_port, self.redis_pass, '-----------------!!!!!2'
        # self.redis_conn = redis.Redis(host='192.168.20.115', port=self.redis_port, password=self.redis_pass)
        self.redis_conn = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_pass)

    def poll(self):
        regex = 'task:*:*:desc'
        for key in self.redis_conn.scan_iter(match=regex):
            lock = self._create_lock_object(key)
            try:
                if lock.acquire(blocking=False):
                    userId = key.split(':')[1]
                    taskId = key.split(':')[2]
                    runningNodeKey = 'task:{userId}:{taskId}:slaveId'.format(userId=userId, taskId=taskId)
                    urllistkey = 'task:{userId}:{taskId}:urllist'.format(userId=userId, taskId=taskId)
                    taskMaxNode = int(self.redis_conn.hget(key, 'taskMaxNode'))   # 此处taskMaxNode已经<=urlNum(第一层调度已处理)
                    status = int(self.redis_conn.hget(key, 'status'))
                    lastTaskMaxNode = int(self.redis_conn.hget(key, 'lastTaskMaxNode'))
                    splited = int(self.redis_conn.hget(key, 'splited'))  # 任务拆分否

                    urlNum = self.redis_conn.llen(urllistkey)
                    runningNodeNum = self.redis_conn.llen(runningNodeKey)


                    # 先判断状态
                    if status == 0:  # 等待执行（将还在执行该任务的所有进程全部终止）  一级调度只是修改了status变为0,taskMaxNode变为0，还未真正通知暂停
                        pass

                    elif status == 1:   # 运行，还没运行但一级调度器已经分配了节点，且状态变位了运行；一直都是运行，只不过分配的节点有变动
                        pass

                    elif status == 2:  # 用户置暂停.    将taskMaxNode清零
                        taskMaxNode = 0
                        self.redis_conn.hset(key, 'taskMaxNode', taskMaxNode)
                    elif status == 3:  # 完成.
                        continue
                    elif status == 4:  # 可删除.         删除与该任务相关的所有key
                        # self.redis_conn.delete(key)
                        # self.redis_conn.delete(runningNodeKey)
                        self.redis_conn.delete(urllistkey)
                        continue

                    if (splited == 2 or splited == 1) and urlNum == 0 and runningNodeNum == 0:   # 任务完成
                        self.redis_conn.hset(key, 'status', '3')
                        self.redis_conn.hset(key, 'endTimeStamp', datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'))
                        continue

                    if splited == 0:   # 表明任务不能拆，启动任务，并将splited置为2(表明该任务启动,)
                        # 在从节点中选取负载较小的物理机，进行分配进程, 待完善！
                        # slaveId = random.randint(0, 12)
                        slaveId = 1
                        dispatch_key = 'dispatch:{slaveId}:{userId}:{taskId}:{uuid}'. \
                            format(slaveId=slaveId, userId=userId, taskId=taskId, uuid=str(uuid.uuid4()).split('-')[4])
                        self.redis_conn.set(dispatch_key, 'start')
                        self.redis_conn.hset(key, 'splited', 2)

                    elif splited == 1:  # 表明可拆分的任务
                        if taskMaxNode != lastTaskMaxNode:      # 为该任务分配的节点有变动
                            if urlNum != 0 and taskMaxNode > runningNodeNum:  # 有子任务，并且最大运行节点数>正在运行节点数，增加节点(进程)
                                addProcessNum = taskMaxNode-runningNodeNum
                                for i in range(addProcessNum):
                                    # 在从节点中选取负载较小的物理机，进行分配进程, 待完善！
                                    # slaveId = random.randint(0, 12)
                                    slaveId = 1
                                    dispatch_key = 'dispatch:{slaveId}:{userId}:{taskId}:{uuid}'.\
                                        format(slaveId=slaveId, userId=userId, taskId=taskId, uuid=str(uuid.uuid4()).split('-')[4])
                                    self.redis_conn.set(dispatch_key, 'start')  # 用于标识要启动哪台物理机，爬取哪个用户的哪个任务

                            elif taskMaxNode < runningNodeNum:         # 最大运行节点数<正在运行节点数，将部分进程终止
                                stopProcessNum = runningNodeNum - taskMaxNode
                                runningNodeList = self.redis_conn.lrange(runningNodeKey, 0, -1)
                                for i in range(stopProcessNum):
                                    if len(runningNodeList) == 0:
                                        break
                                    runningNode = runningNodeList.pop()
                                    slaveId = runningNode.split('&')[0]
                                    pId = runningNode.split('&')[1]
                                    dispatch_key = 'dispatch:{slaveId}:{userId}:{taskId}:{uuid}'.\
                                        format(slaveId=slaveId, userId=userId, taskId=taskId, uuid=str(uuid.uuid4()).split('-')[4])
                                    dispatch_value = 'stop&{pId}'.format(pId=pId)
                                    self.redis_conn.set(dispatch_key, dispatch_value)   # 发起 让某进程终止

                            self.redis_conn.hset(key, 'lastTaskMaxNode', taskMaxNode)   # 实际的节点信息并未改变
                    # task:{userId}:{taskId}:slaveId 里的值最终由从节点的管理器修改
            except Exception:
                print 'redis Exception2'
            # remove lock regardless of if exception or was handled ok
            if lock._held:
                print "releasing2 lock"
                lock.release()

    def _create_lock_object(self, key):
        '''
        Returns a lock object, split for testing
        '''
        return redis_lock.Lock(self.redis_conn, key,
                               expire=REDIS_LOCK_EXPIRATION,
                               auto_renewal=True)

    # 通过watch机制实现redis的互斥修改
    def _watch_redis(self, key):
        with self.redis_con.pipeline() as pipe:
            while 1:
                try:
                    pipe.watch(key)
                    pipe.multi()
                    a = pipe.lrange('task:1:1:urllist', 0, -1)
                    pipe.execute()
                    break
                except Exception:
                    continue

    def next(self):
        pass


def get_local_ip(ifname='enp1s0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    return socket.inet_ntoa(inet[20:24])
