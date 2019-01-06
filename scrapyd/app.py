from twisted.application.service import Application
from twisted.application.internet import TimerService, TCPServer

from .interfaces import IPoller

from .poller import QueuePoller, TaskPoller

from .config import Config
from twisted.web import server
from scrapyd.website import Root
from twisted.python import log
# from scrapy.utils.misc import load_object

def application(config):
    app = Application("Scrapyd")
    poll_interval = config.getfloat('poll_interval', 5)

    poller = QueuePoller(config, app)
    taskpoller = TaskPoller(config, app)   #

    app.setComponent(IPoller, poller)
    app.setComponent(IPoller, taskpoller)    #

    timer = TimerService(poll_interval, poller.poll)
    tasktimer = TimerService(poll_interval, taskpoller.poll)  #

    timer.setServiceParent(app)
    tasktimer.setServiceParent(app)   #

    http_port = config.getint('http_port', 9090)
    bind_address = config.get('bind_address', '127.0.0.1')
    log.msg(format="Scrapyd web console available at http://%(bind_address)s:%(http_port)s/",
            bind_address=bind_address, http_port=http_port)
    webservice = TCPServer(http_port, server.Site(Root(config, app)), interface=bind_address)
    webservice.setServiceParent(app)
    return app
