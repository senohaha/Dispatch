# -*- coding: utf-8 -*-
import redis
import uuid
import datetime
import random
from collections import OrderedDict
import json

def get_wait_task(self, userTaskKey):
    waitTaskids = []
    for userTask in self.redis_conn.scan_iter(match=userTaskKey):
        taskid = userTask.split(':')[2]
        if self.redis_conn.hget(userTask, 'status') == '0':
            waitTaskids.append(taskid)
    return waitTaskids

def get_running_task(self, userTaskKey):
    runningTaskids = []
    for userTask in self.redis_conn.scan_iter(match=userTaskKey):
        taskid = userTask.split(':')[2]
        if self.redis_conn.hget(userTask, 'status') == '1':
            runningTaskids.append(taskid)
    return runningTaskids




if __name__=='__main__':
    redis_conn = redis.StrictRedis(host='192.168.20.111', port=6379)
    regex = 'scheduler:*'
    for key in redis_conn.scan_iter(match=regex):

        try:
            if True:   # 若有其他进程在操作该key，则跳过对该key的处理
                val = redis_conn.hget(key, 'flag')
                userId = key.split(":")[1]
                userTaskKey = 'task:{userId}:*:desc'.format(userId=userId)
                maxNode = int(redis_conn.hget(key, 'maxNode'))
                maxRunTask = int(redis_conn.hget(key, 'maxRunTask'))
                runningTask = int(redis_conn.hget(key, 'runningTask'))

                if val is '1' :   # 若该用户配置改变，或者 存在等待的 并且 运行的任务个数小于用户设置的并行的任务数
                    runningTaskids = get_running_task(userTaskKey)
                    waitTaskids = get_wait_task(userTaskKey)
                    taskNum = len(runningTaskids)+len(waitTaskids)     # 用户 待运行 以及 正在运行 总任务数

                    realMaxRunTask = maxRunTask if maxRunTask < taskNum else taskNum

                    base = maxNode / realMaxRunTask
                    mod = maxNode % realMaxRunTask
                    taskMaxNode = [base+1 if i < mod else base for i in range(realMaxRunTask)]

                    if len(runningTaskids) < realMaxRunTask:   # 如果正在运行的任务个数<分配的最大运行任务数,运行的减少节点，并启动新的任务
                        addRunTask = realMaxRunTask-len(runningTaskids)
                        add_id = 0
                        taskMaxNode_id = 0
                        for taskid in runningTaskids:
                            taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId,taskid=taskid)
                            redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                            taskMaxNode_id += 1
                        for taskid in waitTaskids:
                            if add_id >= addRunTask:
                                break
                            taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                            redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                            redis_conn.hset(taskkey, 'status', 1)
                            add_id += 1
                            taskMaxNode_id += 1
                    else:   # 将部分运行任务变为等待状态，部分运行的任务增加节点
                        real_id = 0
                        taskMaxNode_id = 0
                        for taskid in runningTaskids:
                            taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                            if real_id < realMaxRunTask:
                                redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                                taskMaxNode_id += 1
                                real_id += 1
                            else:
                                redis_conn.hset(taskkey, 'taskMaxNode', 0)
                                redis_conn.hset(taskkey, 'status', 0)
                    redis_conn.hset(key, 'runningTask', realMaxRunTask)
                    redis_conn.hset(key, 'flag', '0')
                elif len(get_running_task(userTaskKey)) < maxRunTask \
                        and len(get_wait_task(userTaskKey)) is not 0:
                    # 存在等待的 并且 运行的任务个数小于用户设置的并行的任务数
                    # 从等待的执行的任务中选出部分启动(将状态变为运行)
                    runningTaskids = get_running_task(userTaskKey)
                    waitTaskids = get_wait_task(userTaskKey)
                    taskNum = len(runningTaskids) + len(waitTaskids)
                    realMaxRunTask = maxRunTask if maxRunTask < taskNum else taskNum
                    runNode = 0

                    for taskid in runningTaskids:
                        taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                        runNode = runNode + int(redis_conn.hget(taskkey, 'taskMaxNode'))
                    leftNode = maxNode-runNode
                    addNewTaskNum = realMaxRunTask-len(runningTaskids)
                    base = leftNode / addNewTaskNum
                    mod = leftNode % addNewTaskNum
                    taskMaxNode = [base + 1 if i < mod else base for i in range(addNewTaskNum)]
                    add_id = 0
                    taskMaxNode_id = 0
                    for taskid in waitTaskids:
                        if add_id >= addNewTaskNum:
                            break
                        taskkey = 'task:{userId}:{taskid}:desc'.format(userId=userId, taskid=taskid)
                        redis_conn.hset(taskkey, 'taskMaxNode', taskMaxNode[taskMaxNode_id])
                        redis_conn.hset(taskkey, 'status', 1)
                        add_id += 1
                        taskMaxNode_id += 1
                    redis_conn.hset(key, 'runningTask', realMaxRunTask)

        except Exception:
            # self.logger.error(traceback.format_exc())
            # self._increment_fail_stat('{k}:{v}'.format(k=key, v=val))
            #
            # self._process_failures(key)
            print 'redis Exception'



