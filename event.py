# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchAttributeException, NoSuchElementException, SessionNotCreatedException, \
    WebDriverException
from collections import OrderedDict
import json
import time
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
import time
import uuid
import redis
import re
import threading
import sys
import redis
from threading import Thread

class Event(object):
    def __init__(self, appid, crawlid):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 10)

        self.server = pymongo.MongoClient()
        self.db = self.server[appid]
        self.db = self.db[crawlid]


    def getweb(self, url, setting):
        movepageconf = re.compile(r'Movepageconf\d*')
        ifcleanCookie = re.compile(r'ifcleanCookie\d*')
        redefCookieValue = re.compile(r'redefCookieValue \d*')
        try:
            for key, val in setting.items():
                # 是否清除cookie
                if (ifcleanCookie.match(key)):
                    if (val == True):
                        self.driver.delete_all_cookies()
                # 自定义cookie
                if (redefCookieValue.match(key)):
                    self.driver.delete_all_cookies()
                    self.driver.add_cookie(val)
            self.driver.get(url)
            if (setting.get("action")):
                for key, val in setting.get("action").items():
                    # 滑动滚动条
                    if (movepageconf.match(key)):
                        count = val.get("movesum")
                        movespace = val.get("movespace")
                        for i in range(count):
                            js = "document.documentElement.scrollTop=" + str(val.get("movedec") * (i + 1)) + ""
                            self.driver.execute_script(js)
                            time.sleep(movespace)
        except TimeoutException:
            self.getweb(url, setting)

    # 点击事件
    def click_event(self, xpath):
        submit = self.wait.until(
            EC.element_to_be_clickable((By.XPATH,xpath))
        )
        submit.click()

    # 输入文字
    def input_text(self, xpath, text):
        inputtext = self.wait.until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        # inputtext.clear()  # 清除输入框中的内容
        inputtext.send_keys(text.decode('utf-8'))

    # 鼠标悬停到元素上
    def move_to_element(self, xpath):
        tag = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        ActionChains(self.driver).move_to_element(tag).perform()

    # 循环点击下一页无子动作
    def loop_click(self, xpath):
        try:
            while True:
                # target = driver.find_element_by_css_selector(css)
                # driver.execute_script("arguments[0].scrollIntoView();", target)
                js = "var q=document.body.scrollTop=100000"
                self.driver.execute_script(js)
                time.sleep(3)
                next_page = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )

                # driver.find_element_by_css_selector(css).send_keys(Keys.TAB)
                current_page1 = self.driver.page_source
                # print driver.page_source
                next_page.click()
                next_page = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                current_page2 = self.driver.page_source
                # print driver.page_source
                if (current_page1 != current_page2):
                    continue
                else:
                    break
        except TimeoutException:
            print u"超时"

    # 循环点击第一页有子动作
    def loop_click2(self, xpath):
        try:

            # target = driver.find_element_by_css_selector(css)
            # driver.execute_script("arguments[0].scrollIntoView();", target)
            js = "var q=document.body.scrollTop=100000"
            self.driver.execute_script(js)
            time.sleep(3)
            next_page = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            next_page.click()
        except TimeoutException:
            print u"超时"

    def _crawl_text(self, xpath):
        try:
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except:
            print u'字段提取失败'
            return None

        return self.driver.find_element(By.XPATH, xpath).text

    def _crawl_href(self, xpath):
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return self.driver.find_element(By.XPATH, xpath).get_attribute('href')

    def _crawl_img_href(self, xpath):
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return self.driver.find_element(By.XPATH, xpath).get_attribute('src')

    def crawl_all_text(self, in_xpath, out_xpath):
        in_xpath = in_xpath[len(out_xpath):] + '/a'
        in_xpath = in_xpath.split('/', 1)[1]

        text_list = []
        elements = self.driver.find_elements(By.XPATH, out_xpath)
        for ele in elements:
            try:
                text = ele.find_element(By.XPATH, in_xpath).text
            except NoSuchElementException or NoSuchAttributeException:
                return None  # ti qu de bu shi lian jie
            text_list.append(text)
        # print text_list
        return text_list

    def crawl_all_img_href(self, in_xpath, out_xpath):
        in_xpath = in_xpath[len(out_xpath):] + '/img'
        in_xpath = in_xpath.split('/', 1)[1]

        img_href_list = []
        elements = self.driver.find_elements(By.XPATH, out_xpath)
        for ele in elements:
            try:
                img_href = ele.find_element(By.XPATH, in_xpath).get_attribute('src')
            except NoSuchElementException or NoSuchAttributeException:
                return None  # ti qu de bu shi lian jie
            img_href_list.append(img_href)
        # print img_href_list
        return img_href_list

    def crawl_all_href(self, in_xpath, out_xpath):
        # consider not li
        # if re.match(r'.*/a$', xpath):  # ti lian jie de xpath
        #     url = driver.find_element(By.XPATH, xpath).get_attribute('href')
        #     return [url, ]
        in_xpath = in_xpath[len(out_xpath):] + '/a'
        in_xpath = in_xpath.split('/', 1)[1]

        url_list = []
        elements = self.driver.find_elements(By.XPATH, out_xpath)
        for ele in elements:
            try:
                url = ele.find_element(By.XPATH, in_xpath).get_attribute('href')
            except NoSuchElementException or NoSuchAttributeException:
                return None      # 所给提取规则提取的不是链接
            url_list.append(url)
        # print len(url_list)
        return url_list

    def crawl(self, jsondata):
        item = {}
        dictdata = json.loads(jsondata, object_pairs_hook=OrderedDict)
        param = dictdata['op_param']
        if len(param):
            hrefs = param['href']
            for name, xpath in hrefs.items():
                if isinstance(xpath, dict):
                    in_xpath = xpath['in_xpath']
                    out_xpath = xpath['out_xpath']
                    item[name] = self.crawl_all_href(in_xpath, out_xpath)
                else:
                    item[name] = self._crawl_href(xpath)

            texts = param['text']
            for name, xpath in texts.items():
                if isinstance(xpath, dict):
                    in_xpath = xpath['in_xpath']
                    out_xpath = xpath['out_xpath']
                    item[name] = self.crawl_all_text(in_xpath, out_xpath)
                else:
                    item[name] = self._crawl_text(xpath)

            img_hrefs = param['img_href']
            for name, xpath in img_hrefs.items():
                if isinstance(xpath, dict):
                    in_xpath = xpath['in_xpath']
                    out_xpath = xpath['out_xpath']
                    item[name] = self.crawl_all_img_href(in_xpath, out_xpath)
                else:
                    item[name] = self._crawl_img_href(xpath)
            # print item
            # print '++++++++++++++++++++'
            self.db.insert(item)
        else:
            print '没有可爬取的字段'

    def loop_crawl(self, jsondata):
        dictdata = json.loads(jsondata, object_pairs_hook=OrderedDict)
        current_url = self.driver.current_url
        if len(dictdata['op_param']):
            in_xpath = dictdata['op_param']['in_xpath']
            out_xpath = dictdata['op_param']['out_xpath']
            url_list = self.crawl_all_href(in_xpath, out_xpath)
            # print url_list
            if isinstance(url_list, list):
                for url in url_list:
                    self.driver.get(url)  # need change to getweb() in the futher!!!!!!!!!!!!
                    self.crawl(json.dumps(dictdata['sub_opList']['crawl']))
            else:
                print '提供的提取规则，提取的不是链接'

        else:
            print '没有可循环的元素'

        return current_url

    # 关闭driver
    def close(self):
        self.driver.close()




class Execute(object):
    # def __init__(self, appid, crawlid):
    #     self.event = Event(appid, crawlid)
    def __init__(self):
        self.redis = redis.Redis(host='192.168.1.138',port=6379)


    def execute(self, appid, crawlid):
        self.event = Event(appid, crawlid)
        # print type(task), 'event!!!!'
        # print task,'hahadfy'
        """{u'opList': {u'loopcrawl': {u'sub_opList': {u'crawl': {u'op_param': {
            u'text': {u'tcheng': u'//*[@id="Labeltc"]', u'\u7f51\u9875': u'//*[@id="Labelxb"]',
                      u'name': u'//*[@id="Labeldsxm"]', u'xuesjl': u'//*[@id="Labelxsjl"]'}, u'href': {},
            u'img_href': {}}}}, u'op_param': {
            u'in_xpath': u'/html/body/form/div[3]/div[2]/div[2]/div[2]/table/tbody/tr[3]/td/div[1]',
            u'out_xpath': u'/html/body/form/div[3]/div[2]/div[2]/div[2]/table/tbody/tr[3]/td/div'}},
                     u'openweb': {u'op_param': {u'URL': u'http://222.197.183.99/TutorList.aspx'}, u'op_setting': {
                         u'action': {u'Movepageconf': {u'movedec': 1000, u'movespace': 3, u'movesum': 3}},
                         u'ifcleanCookie': True, u'ifBlockAD': True, u'timeout': 500}, u'op_type': 1}}}
        """
        key = "{sid}:{crawlid}:queue".format(sid=appid, crawlid=crawlid)
        task = self.redis.get(key)  # str
        # self.redis.delete(key)

        option = json.loads(task, object_pairs_hook=OrderedDict)
        openweb = re.compile(r'openweb\d*')
        inputtext = re.compile(r'inputtext\d*')
        clickevent = re.compile(r'clickevent\d*')
        loopclick = re.compile(r'loopclick\d*')
        movetoelement = re.compile(r'movetoelement\d*')
        loopcrawl = re.compile(r'loopcrawl\d*')
        crawl = re.compile(r'crawl\d*')
        close = re.compile(r'close\d*')
        try:
            for key, val in option.get('opList').items():

                # 打开网页
                if openweb.match(key):
                    self.event.getweb(val.get("op_param").get("URL"), val.get("op_setting"))
                # 输入文字
                if inputtext.match(key):
                    param = val.get("op_param")
                    self.event.input_text(param.get("xpath"), param.get("text"))
                # 点击事件
                if clickevent.match(key):
                    # print val.get('op_param').get('css')
                    self.event.click_event(val.get("op_param").get("xpath"))
                # 鼠标悬停事件
                if movetoelement.match(key):
                    self.event.move_to_element(val.get("op_param").get("xpath"))
                # 关闭网页
                if close.match(key):
                    self.event.close()
                # 循环点击
                if loopclick.match(key):
                    if val.has_key("sub_opList"):
                        sub = val.get("sub_opList")
                        while True:
                            for key2, val2 in sub.items():
                                if loopcrawl.match(key2):
                                    url = self.event.loop_crawl(json.dumps(val2))
                                    print url
                                    self.event.driver.get(url)
                                if crawl.match(key2):
                                    self.event.crawl(json.dumps(val2))
                            current_page1 = self.event.driver.page_source
                            self.event.loop_click2(val.get("op_param").get("xpath"))
                            current_page2 = self.event.driver.page_source
                            if current_page1 != current_page2:
                                continue
                            else:
                                break
                    else:
                        self.event.loop_click(val.get("op_param").get("xpath"))

                if loopcrawl.match(key):
                    self.event.loop_crawl(json.dumps(val))

                if crawl.match(key):
                    self.event.crawl(json.dumps(val))
        except SessionNotCreatedException as e:
            print '用户:', appid, '强制终止任务:', crawlid, '线程:', threading.currentThread().name
        except WebDriverException as e:
            print '用户:', appid, '强制终止任务:', crawlid, '线程:', threading.currentThread().name


if __name__ == "__main__":
    appid = sys.argv[1]
    crawlid = sys.argv[2]

    # Execute().execute('dfyh', '222')
    Execute().execute(appid, crawlid)