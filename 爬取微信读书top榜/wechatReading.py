import re
import requests
from time import sleep
import time
from lxml import etree
import csv
from bs4 import BeautifulSoup
import threading
import multiprocessing
from wordcloud import WordCloud
import PIL.Image as image
import numpy as np
import jieba
from matplotlib import colors
import random


headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko)'   
            'Chrome/65.0.3325.162 Safari/537.36'
          }
# ajax动态加载爬取
page_urls = ['https://weread.qq.com/web/category/' + str(i * 100000) for i in range(1, 18)] #前20本得爬取
ajax_urls = ['https://weread.qq.com/web/bookListInCategory/{0}?maxIndex={1}'.format(i * 100000, j) for i in range(1, 18)
             for j in range(20, 200, 20)]
hashtable = {'order': 0, 'author': 1, 'Book_name': 2, 'recommend': 3, 'Reading_people': 4, 'info': 5, 'cover': 6}

# 构造正则表达式匹配字符串
index_path = re.compile('"searchIdx":(\d+)')
name_path = re.compile('"title":"(.*?)"')
author_path = re.compile('"author":"(.*?)"')
good = re.compile('"good":(\d+)')
fair = re.compile('"fair":(\d+)')
poor = re.compile('"poor":(\d+)')
number_path = re.compile('"readingCount":(\d+)')
info_path = re.compile('"intro":"(.*?)"', re.S)
img_path = re.compile('"cover":"(.*?)"')
thread_list = []


class Behindpause (threading.Thread):
    """创建多线程爬取分页内容"""
    def __init__(self, url, move, exit='rank=1', type = 'all' ):
        """
        :param url: 爬取得路径
        :param move: 分页得偏移量，一个xhr文件包含20本书
        :param exit: 网页标识，在爬取别的榜单时修改
        :param type: 爬取榜单得类型
        """
        threading.Thread.__init__(self)
        self.move = move
        self.url = url
        self. exit =  exit
        self.type = type

    def run(self):
        print ("开始线程：" + f"{self.move}-{self.move+20}")
        write(f'all/csv/{self.move}', behindPage(self.move, self.type, self.exit))
        write('all/csv/all', behindPage(self.move, self.type, self.exit), 1)
        pictures(behindPage(self.move, self.type, self.exit))
        print ("退出线程：" + f"{self.move}-{self.move+20}")


def frontPage(page_url):
    '''
    爬取前二十本得页面，使用xpath模块
    '''
    data1 = []
    # self.lock.acquire()
    # page_url = self.page_queue.get()
    # print(page_url)
    # self.lock.release()
    req1 = requests.get(page_url, headers=headers)
    page_text = req1.text # 获取原始文本
    # print(page_text)
    html = etree.HTML(page_text) # 自动修正文本
    # soup = BeautifulSoup(url,'lxml')
    # 序号
    index_s = html.xpath('//p[@class="wr_bookList_item_index"]/text()')
    data1.append(index_s)
    # 作者
    authors = html.xpath('//p[@class="wr_bookList_item_author"]/a/text()')
    data1.append(authors)
    # 书名
    names = html.xpath('//p[@class="wr_bookList_item_title"]/text()')
    data1.append(names)
    # 推荐度
    scores = html.xpath('//span[@class="wr_bookList_item_reading_percent"]/text()')
    data1.append(scores)
    # 在读人数
    numbers = html.xpath('//span[@class="wr_bookList_item_reading_number"]/text()')
    data1.append(numbers)
    # 内容简介
    infos = html.xpath('//p[@class="wr_bookList_item_desc"]/text()')
    data1.append(infos)
    # 图片链接
    imgs = html.xpath('//div[@class="wr_bookCover wr_bookList_item_cover"]/img/@src')
    data1.append(imgs)

    search = page_url.split('/')[-1]
    data1.append(search)
    # print(data1)
    return data1
def behindPage(move=0,type = 'all',exit = 'rank=1'):
    ajax_url = f'https://weread.qq.com/web/bookListInCategory/{type}?maxIndex={move}&{exit}'
    data2 = []
    # self.lock.acquire()
    # ajax_url = self.ajax_queue.get()
    # print(ajax_url)
    # self.lock.release()
    req2 = requests.get(ajax_url, headers=headers)
    resp = req2.text
    # 序号
    index_s = re.findall(index_path, resp)
    data2.append(index_s)
    # 作者
    authors = re.findall(author_path, resp)
    data2.append(authors)
    # 书名
    names = re.findall(name_path, resp)
    data2.append(names[0::2])
    #推荐度
    goods = re.findall(good, resp)
    fairs = re.findall(fair, resp)
    poors  = re.findall(poor, resp)
    scores = [f"{round((int(i)+int(j)*0.1-int(k))/(int(i)+int(k)+int(j))*100,1)}%"
              for i,j,k in zip(goods,fairs,poors)]
    # scores_convert = []
    # for score in scores:
    #     score = str(float(score) / 10)
    #     scores_convert.append(score)
    data2.append(scores)
    # 在读人数
    numbers = re.findall(number_path, resp)
    numbers_newlist = []
    for people in numbers:
        # 类型转换成浮点型
        people = float(people)
        if people < 10:
            people = people*10000
            # 类型转换回str
            people = int(people)
            numbers_newlist.append(round(people))
        else:
            numbers_newlist.append(round(people))
    data2.append(numbers_newlist)
    # 内容简介
    infos = re.findall(info_path, resp)
    data2.append(infos)
    # 图片链接
    images = re.findall(img_path, resp)
    data2.append(images)
    # 附加信息
    search = ajax_url.split('/')[-1].split('?')[0]
    data2.append(search)
    start_index = ajax_url.split('=')[-1]
    data2.append(start_index)
    # print(data2)
    return data2
def pictures(data):
    """
    爬取图片资源
    :param data: 返回的数据列表
    :return: none
    """
    bookName = data[2]
    images = data[6]
    index = data[0]
    for i in range(0,len(images)):
        pic = requests.get(images[i].replace('/s_','/t6_'))
        with open("result/all/images/"+f"{index[i]}.{bookName[i]}.jpg", 'wb+') as f:
            print(f'正在保存--{bookName[i]}--封面图片')
            f.write(pic.content)
def write(name,data,title=0):
    """
    :param name: 保存文件得名称
    :param data: 数据存储列表
    :param title: 是否写入标题
    :return:
    """
    with open('result/'+ name +'.csv', 'a', encoding='utf-8') as f:
        print(f'正在写{name}.csv文件')
        if title == 0:
            f.write('order,author,Book_name,recommend,Reading_people,info,cover\n')
        order = data[0]
        author = data[1]
        bookName = data[2]
        recommend = data[3]
        reading_people = data[4]
        infos = data[5]
        img_link = data[6]
        for i in range(0,len(order)):
            print(f'正在写入第{i}行')
            f.write(f"{order[i]},{author[i]},{bookName[i].strip()},{recommend[i]},{reading_people[i]},{infos[i].strip().replace(',','，')},{img_link[i].replace('/s_','/t6_')}")
            f.write('\n')
def ThreadingPause():
    """使用多线程得方式爬取微信读书"""
    url = 'https://weread.qq.com/web/category/all'
    ajax_url = 'https://weread.qq.com/web/bookListInCategory/all?maxIndex=20&rank=1'
    threading_list = []
    for move in range(20, 200, 20):
        thread_pause = Behindpause(ajax_url, move)
        threading_list.append(thread_pause)
        thread_pause.start()
    while threading_list:
        threading_list[0].join()
        threading_list.pop(0)
    end_time = time.time()
    print('爬取时间共花费{}'.format(end_time - start_time))
def NormalPause():
    """
    一般的爬取方式
    :return:
    """
    for i in range(20,200,20):
        write(f'all/csv/{i}', behindPage(i))
        write('all/csv/all', behindPage(i),1)
        pictures(behindPage(i))
    end_time = time.time()
    print('爬取时间共花费{}'.format(end_time - start_time))
def FrontPage():
    """
    爬取前二十本书籍的函数
    :return:
    """
    url = 'https://weread.qq.com/web/category/all'
    ajax_url = 'https://weread.qq.com/web/bookListInCategory/all?maxIndex=20&rank=1'
    frontPage(url)
    write('all//csv/all', frontPage(url))
    write('all/csv/0',frontPage(url))
    pictures(frontPage(url))
    print('* ' * 15 + ' 前20册已爬取完毕 ' + '* ' * 15)

def Readcsv(*col):
    """按照列读取csv文件"""
    with open('result/all/csv/all.csv', 'r', encoding="utf-8") as f:
        data1 = []
        reader = csv.reader(f)
        for row in reader:
            for i in col:
                line = row[i]
                # print("_________________",end='')
                data1.append(line)
                print(line+" | ",end='')
            print('\n')
    return data1

def WriteCsv(data,filename):
    with open(f"result/all/csv/{filename}.csv",'w+',encoding='utf-8') as f:
        for i in data:
            f.write(i+' ')

def Select(parameter, vaule='*',*j):
    """
    检索信息的函数
    :param parameter: 要查询的参数
    :param vaule: 目标检索值
    :param j:查询的参数
    :return:
    """
    if vaule == '*':
        Readcsv(hashtable[parameter])

    with open('result/all/csv/all.csv', 'r', encoding="utf-8") as csvfile:
        data = []
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row[parameter] == vaule:
                print('-' * len(row['info']))
                for i in j:
                    print(f"{i}:"+'\t'+row[i])
                    data.append(row[i])
                print('-'*len(row['info']))
                print('\n')
        return data

# 分词
def trans_CN(text):
    # 接收分词的字符串
    word_list = jieba.cut(text)
    # 分词后在单独个体之间加上空格
    result = " ".join(word_list)
    return result

def Worldcloud(filename,key = 0):
    # 建立颜色数组，可更改颜色
    # 莫兰迪配色
    color_list1 = ['#6F808E','#80919F','#B6D0E7','#97A0A5']
    # Turner配色系1
    color_list2 = ['#C3C0AF','#D3B78F','#E3C167','#CF8C71','#95B2B0']
    # Turner配色系2
    color_list3 = ['#E6B8A0','#6D8398','#A49FB3','#C0C0C8','#B8B0B0']
    # 沁园春配色
    color_list4 = ['#76A4B3','#D7E8F8','#205064','#ECA7A7',]
    # 醉花阴配色
    color_list5 = ['#FCB48E','#EC776E','#92A470','#FFBC8F']
    # 随机选取色系数组
    ColorArray = [color_list1,color_list2,color_list3,color_list4,color_list5]

    # 调用
    colormap = colors.ListedColormap(ColorArray[random.randint(0,4)])

    if key == 1:
        WriteCsv(Select('Book_name', filename, 'info'), filename)
        with open(f"result/all/csv/{filename}.csv", 'r', encoding='utf-8') as fp:
            text = fp.read()
            # 将读取的中文文档进行分词
            text = trans_CN(text)
            mask2 = np.array(image.open("result/cat.png"))
            wordcloud = WordCloud(
                # 添加遮罩层
                mask=mask2,
                # 生成中文字的字体,必须要加,不然看不到中文
                font_path="C:\Windows\Fonts\STXINGKA.TTF",
                contour_width=3,
                colormap=colormap,
                contour_color=random.choice(color_list3),
                background_color="white",
            ).generate(text)
            image_produce = wordcloud.to_image()
            image_produce.show()
            return

    WriteCsv(Readcsv(hashtable[filename]),filename)
    with open(f"result/all/csv/{filename}.csv", 'r', encoding='utf-8') as fp:
        text = fp.read()
        # print(text)
        # 将读取的中文文档进行分词
        text = trans_CN(text)
        mask = np.array(image.open("result/tl.png"))
        wordcloud = WordCloud(
            # 添加遮罩层
            mask=mask,
            # 生成中文字的字体,必须要加,不然看不到中文
            # font_path="C:\Windows\Fonts\STXINGKA.TTF",
            font_path="STXINWEI.TTF",
            width=1000,
            height=800,
            max_words=150,
            max_font_size=100,
            # min_font_size=20,
            contour_width=3,
            colormap = colormap,
            contour_color=random.choice(['white','#7F9DB9']),
            background_color="black",
        ).generate(text)
        image_produce = wordcloud.to_image()
        image_produce.show()

if __name__ == '__main__':
    start_time = time.time()
    # 爬取前20册得书籍
    FrontPage()
    # 采用多线程方式爬取
    ThreadingPause()
    # 采用普通方式爬取
    NormalPause()
    # 按照列读取文件
    Readcsv(6)
    # 书籍查询
    Select('order','10','author','Book_name','recommend')
    Select('author','刘慈欣','Book_name')
    # 生成词云
    Worldcloud('author')
    Worldcloud('人类简史：从动物到上帝',1)
    Worldcloud('追风筝的人',1)







