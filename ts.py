# !/usr/bin/env python
# !/usr/bin/python
# -*-coding:utf-8-*-

import sys

from datetime import datetime
from twisted.python import log
log.startLogging(sys.stdout)
from multiprocessing import cpu_count
from twisted.internet import protocol, reactor, defer, error
from twisted.application.service import Service

Max_Proc_Per_Cpu = 4
Max_Proc = 10

# class Launcher(Service):
#     name = 'launcher'
#
#     def __init__(self, app):
#         self.processes = []
#
#     # def startService(self):
#     #     log.msg(format='Scrapyd  started',
#     #             system='Launcher')
#
#     def spawn_process(self, uuid, crawlid):
#
#         arg = ['/usr/bin/python2.7', '/root/Desktop/scrapyd-master_3_socket/sub.py', uuid, crawlid]
#
#         pp = ScrapyProcessProtocol('slot', 'project', 'spider', 'job', 'env')
#         pp.deferred.addBoth(self._process_finished, pp)
#
#         reactor.spawnProcess(pp, '/usr/bin/python2.7', arg)
#
#         self.processes.append(pp)
#
#     def _process_finished(self, _, pp):
#         self.processes.pop(pp)
#         pp.end_time = datetime.now()
#
#     def _get_max_proc(self):
#         max_proc = Max_Proc
#         if not max_proc:
#             try:
#                 cpus = cpu_count()
#             except NotImplementedError:
#                 cpus = 1
#             max_proc = cpus * Max_Proc_Per_Cpu
#         return max_proc



class ScrapyProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, slot, project, spider, job, env):
        self.slot = slot
        self.pid = None
        self.project = project
        self.spider = spider
        self.job = job
        self.start_time = datetime.now()
        self.end_time = None
        self.env = env
        self.logfile = 'SCRAPY_LOG_FILE'
        self.itemsfile = 'SCRAPY_FEED_URI'
        self.deferred = defer.Deferred()

    def connectionMade(self):
        self.pid = self.transport.pid
        self.log("Process started: ")

    def outReceived(self, data):  #
        log.msg(data.rstrip(), system="Launcher,%d/stdout" % self.pid)

    def errReceived(self, data):
        log.msg(data.rstrip(), system="Launcher,%d/stderr" % self.pid)


    def processEnded(self, status):
        if isinstance(status.value, error.ProcessDone):
            self.log("Process finished: ")
        else:
            self.log("Process died: exitstatus=%r " % status.value.exitCode)
        self.deferred.callback(self)

    def log(self, action):
        fmt = '%(action)s project=%(project)r spider=%(spider)r job=%(job)r pid=%(pid)r log=%(log)r items=%(items)r'
        log.msg(format=fmt, action=action, project=self.project, spider=self.spider,
                job=self.job, pid=self.pid, log=self.logfile, items=self.itemsfile)



def main():

    pp = ScrapyProcessProtocol('slot', 'project', 'spider', 'job', 'env')
    import os
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    aa = '333'
    bbb = 'www'
    reactor.spawnProcess(pp, '/usr/bin/python2.7', ['/usr/bin/python2.7', '/root/Desktop/version_1_custom_crawl/Slave_manager/sub.py',aa,bbb],env = env)
    reactor.run()

if __name__ == "__main__":
    main()


