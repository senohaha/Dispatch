# -*- coding: utf-8 -*-
import redis
import redis_lock
import redis
import uuid
import datetime
import random
from collections import OrderedDict
import json
redis_conn = redis.Redis()

# map1 = {'taskMaxNode': '3', 'runningNode': '2', 'status': '1', 'endTimeStamp': '0'}
# map2 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map3 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map4 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map5 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map6 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map7 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
# map8 = {'taskMaxNode': '3', 'runningNode': '0', 'status': '1', 'endTimeStamp': '0'}
#
#
# redis_con.hmset('task:1:1:desc', map1)
# # redis_con.hmset('task:1:1:desc', map2)
# # redis_con.hmset('task:1:1:desc', map3)
# # redis_con.hmset('task:1:1:desc', map4)
# # redis_con.hmset('task:1:1:desc', map5)
# # redis_con.hmset('task:1:1:desc', map6)
# # redis_con.hmset('task:1:1:desc', map7)
# # redis_con.hmset('task:1:1:desc', map8)
#
#
# redis_con.lpush('task:1:1:slaveId', '127&p1', '137&p2')
#
# redis_con.lpush('task:1:1:urllist', '111', '2222', '333','4444','555')
regex = 'task:*:*:desc'
for key in redis_conn.scan_iter(match=regex):
    userId = key.split(':')[1]
    taskId = key.split(':')[2]
    runningNodeKey = 'task:{userId}:{taskId}:slaveId'.format(userId=userId, taskId=taskId)
    urllistkey = 'task:{userId}:{taskId}:urllist'.format(userId=userId, taskId=taskId)
    taskMaxNode = int(redis_conn.hget(key, 'taskMaxNode'))   # 此处taskMaxNode已经<=urlNum(第一层调度已处理)
    status = int(redis_conn.hget(key, 'status'))

    urlNum = redis_conn.llen(urllistkey)
    runningNodeNum = redis_conn.llen(runningNodeKey)


    # 先判断状态
    if status is 0:  # 等待执行（将还在执行该任务的所有进程全部终止）  一级调度只是修改了status变为0,taskMaxNode变为0，还未真正通知暂停
        pass

    elif status is 1:   # 运行，还没运行但一级调度器已经分配了节点，且状态变位了运行；一直都是运行，只不过分配的节点有变动
        pass

    elif status is 2:  # 用户置暂停.    将taskMaxNode清零
        taskMaxNode = 0
        redis_conn.hset(key, 'taskMaxNode', taskMaxNode)
    elif status is 3:  # 完成.
        continue
    elif status is 4:  # 可删除.         删除与该任务相关的所有key
        redis_conn.delete(key)
        redis_conn.delete(runningNodeKey)
        redis_conn.delete(urllistkey)

    if urlNum is 0 and runningNodeNum is 0:   # 任务完成
        redis_conn.hset(key, 'status', '3')
        redis_conn.hset(key, 'endTimeStamp', datetime.datetime.now())
        continue

    if taskMaxNode is not runningNodeNum:      # 为该任务分配的节点有变动
        if urlNum is not 0 and taskMaxNode > runningNodeNum:  # 有子任务，并且最大运行节点数>正在运行节点数，增加节点(进程)
            addProcessNum = taskMaxNode-runningNodeNum
            for i in range(addProcessNum):
                # 在从节点中选取负载较小的物理机，进行分配进程, 待完善！
                slaveId = random.randint(0, 12)
                dispatch_key = 'dispatch:{slaveId}:{userId}:{taskId}:{uuid}'.\
                    format(slaveId=slaveId, userId=userId, taskId=taskMaxNode,uuid=str(uuid.uuid4()).split('-')[4])
                redis_conn.set(dispatch_key, 'start')  # 用于标识要启动哪台物理机，爬取哪个用户的哪个任务

        elif taskMaxNode < runningNodeNum:         # 最大运行节点数<正在运行节点数，将部分进程终止
            stopProcessNum = runningNodeNum - taskMaxNode
            runningNodeList = redis_conn.lrange(runningNodeKey, 0, -1)
            for i in range(stopProcessNum):
                if len(runningNodeList) is 0:
                    break
                runningNode = runningNodeList.pop()
                slaveId = runningNode.split('&')[0]
                pId = runningNode.split('&')[1]
                dispatch_key = 'dispatch:{slaveId}:{userId}:{taskId}:{uuid}'.\
                    format(slaveId=slaveId, userId=userId, taskId=taskId, uuid=str(uuid.uuid4()).split('-')[4])
                dispatch_value = 'stop&{pId}'.format(pId=pId)
                redis_conn.set(dispatch_key, dispatch_value)   # 发起 让某进程终止

        redis_conn.hset(key, 'runningNode', taskMaxNode)
    # task:{userId}:{taskId}:slaveId 里的值最终由从节点的管理器修改



