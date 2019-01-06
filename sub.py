
# !/usr/bin/evn python
# -*-coding:utf-8-*-
import time
from selenium import webdriver
import sys, os
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)


# def main():
#     # running = True
#     #
#     # while running:
#     #     print 'dfy'
#     #     input = sys.stdin.readline().rstrip('\n')
#     #     if input == 'q':
#     #         running = False
#     #     print "You said:%s" % input
#     for i in range(40):
#         import time
#         time.sleep(5)
#         print 'sss   ',i


class Execute(object):
    # def __init__(self, appid, crawlid):
    #     self.event = Event(appid, crawlid)

    def execute(self, appid, crawlid):
        print appid, crawlid, 'aaaaasddfd'
        driver = webdriver.Firefox()
        time.sleep(10)

if __name__ == "__main__":
    appid = sys.argv[1]
    crawlid = sys.argv[2]
    # print appid
    # print crawlid
    Execute().execute(appid, crawlid)
