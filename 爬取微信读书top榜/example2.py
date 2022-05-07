# -*- coding = utf-8 -*-
# @Time: 2021/2/16 11:10
# @File: spider.py
# @Software: PyCharm

import requests
import threading
import random
import queue
from lxml import etree
import re
import xlwt
import time

page_urls = ['https://weread.qq.com/web/category/' + str(i * 100000) for i in range(1, 18)] #前20本得爬取
ajax_urls = ['https://weread.qq.com/web/bookListInCategory/{0}?maxIndex={1}'.format(i * 100000, j) for i in range(1, 18)
             for j in range(20, 200, 20)] # ajax动态加载爬取

USER_AGENT = [
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
]
user_agent = random.choice(USER_AGENT)
headers = {
    'User-Agent': user_agent
}
# 构造正则表达式匹配字符串
index_path = re.compile('"searchIdx":(\d+)')
name_path = re.compile('"title":"(.*?)"')
author_path = re.compile('"author":"(.*?)"')
score_path = re.compile('"star":(\w+)')
number_path = re.compile('"readingCount":(\d+)')
info_path = re.compile('"intro":"(.*?)"', re.S)
thread_list = []

# 保存文件到相应得目录
class save_excel:
    def __init__(self):
        self.book = xlwt.Workbook(encoding='utf-8')  # 创建workbook对象
        self.savepath = "微信读书Top100.xls"
    # 写前20本书
    def writeData1(self, data):
        '''
        建立sheet表，写入data1数据
        '''
        sheet = self.book.add_sheet('微信读书top100_%s' % data[-1], cell_overwrite_ok=True)  # True为每次覆盖以前内容
        col = ('id', '书名', '作者', '评分', '阅读人数', '概况')
        for i in range(0, len(col)):  # 写列名
            print("写%d列" % i)
            sheet.write(0, i, col[i])
            for j in range(0, len(data[i])):
                sheet.write(j + 1, i, data[i][j])

    def writeData2(self, data):
        '''
        追加data2数据
        '''
        sheet = self.book.get_sheet('微信读书top100_%s' % data[-2])
        for i in range(0, 6):  # 写列名
            for j in range(int(data[-1]), int(data[-1]) + len(data[i])):
                sheet.write(j + 1, i, data[i][j - int(data[-1])])

    def saveData(self):
        '''
        保存到文件savepath路径
        '''
        self.book.save(self.savepath)


class crawl_and_parse:
    def __init__(self, page_queue, ajax_queue, lock):
        self.page_queue = page_queue
        self.ajax_queue = ajax_queue
        self.lock = lock

    def spider1(self):
        '''
        输入：page_queue.get()
        --------------------------
        爬取：requests.get
        解析：xpath语法
        --------------------------
        返回一个列表文件data1
        '''
        data1 = []
        self.lock.acquire()
        page_url = self.page_queue.get()
        print(page_url)
        self.lock.release()
        req1 = requests.get(page_url, headers=headers)
        page_text = req1.text
        html = etree.HTML(page_text)
        index_s = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/p/text()')
        data1.append(index_s)
        names = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/div[2]/p[1]/text()')
        data1.append(names)
        authors = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/div[2]/p[2]/a/text()')
        data1.append(authors)
        scores = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/div[2]/p[3]/span[1]/text()')
        data1.append(scores)
        numbers = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/div[2]/p[3]/span[4]/em/text()')
        data1.append(numbers)
        infos = html.xpath('//*[@id="routerView"]/div[2]/ul/li/div[1]/div[2]/p[4]/text()')
        data1.append(infos)
        search = page_url.split('/')[-1]
        data1.append(search)
        return data1

    def spider2(self):
        '''
        输入：ajax_queue.get()
        --------------------------
        爬取：requests.get
        解析：re正则表达式语法
        --------------------------
        返回一个列表文件data2
        '''
        data2 = []
        self.lock.acquire()
        ajax_url = self.ajax_queue.get()
        print(ajax_url)
        self.lock.release()
        req2 = requests.get(ajax_url, headers=headers)
        resp = req2.text
        index_s = re.findall(index_path, resp)
        data2.append(index_s)
        names = re.findall(name_path, resp)
        data2.append(names)
        authors = re.findall(author_path, resp)
        data2.append(authors)
        scores = re.findall(score_path, resp)
        scores_convert = []
        for score in scores:
            score = str(float(score) / 10)
            scores_convert.append(score)
        data2.append(scores_convert)
        numbers = re.findall(number_path, resp)
        data2.append(numbers)
        infos = re.findall(info_path, resp)
        data2.append(infos)
        search = ajax_url.split('/')[-1].split('?')[0]
        data2.append(search)
        start_index = ajax_url.split('=')[-1]
        data2.append(start_index)
        return data2


class spider1(threading.Thread):
    def __init__(self, page_queue, lock, *args, **kwargs):
        super(spider1, self).__init__(*args, **kwargs)
        self.page_queue = page_queue

    def run(self):
        if self.page_queue.empty() != True:
            data1 = crawl_and_parse.spider1()
            save_excel.writeData1(data1)
        else:
            return


class spider2(threading.Thread):
    def __init__(self, ajax_queue, lock, *args, **kwargs):
        super(spider2, self).__init__(*args, **kwargs)
        self.ajax_queue = ajax_queue

    def run(self):
        if self.ajax_queue.empty() != True:
            data2 = crawl_and_parse.spider2()
            save_excel.writeData2(data2)
        else:
            return


if __name__ == '__main__':
    start_time = time.time()
    page_queue = queue.Queue(17)
    ajax_queue = queue.Queue(200)
    lock = threading.Lock()
    save_excel = save_excel()
    crawl_and_parse = crawl_and_parse(page_queue, ajax_queue, lock)

    for page_url in page_urls:
        page_queue.put(page_url)

    for ajax_url in ajax_urls:
        ajax_queue.put(ajax_url)

    for i in range(20):
        th1 = spider1(page_queue, lock, name="爬虫1线程%d" % i)
        thread_list.append(th1)
    for j in range(200):
        th2 = spider2(ajax_queue, lock, name="爬虫2线程%d" % j)
        thread_list.append(th2)

    for t in thread_list:
        t.start()
        t.join()

    save_excel.saveData()
    end_time = time.time()
    print('it costs {}s'.format(end_time - start_time))
