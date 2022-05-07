import re
import requests
import json
from time import sleep

def get_one_page(url):
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko)'   
            'Chrome/65.0.3325.162 Safari/537.36'
    }
    # 使用request get方法爬取
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def parse_one_page(html):
    # 匹配模式1：匹配图书的序号，图片链接，图书名，
    pattern1 = re.compile('<p.*wr_bookList_item_index.*?>(.*?)</p>'+
                          '.*img src="(.*?)".*<p.*wr_bookList_item_title.*?>(.*?)</p>'+
                          '.*<a.*>(.*)</a>'+
                          '.*<span.*wr_bookList_item_reading_number">(.*?)</span>')
    items1 = re.findall(pattern1, html)
    # items2 = re.findall(pattern2, html)
    for item in items1:
        if float(item[4]) < 10:
            num = str(int(float(item[4]) * 10000))
        else:
            num = item[4]
        yield [
            item[0],
            item[1],
            item[2],
            item[3],
            num
        ]
    # items = re.match(pattern,html)
    # print(items1)
    # print(items3)
    # print(items2)

# 爬取推荐指数
def parse_one_page_content(html):
    # 匹配模式2：匹配相关推荐词
    pattern2 = re.compile('.*<p class="wr_bookList_item_desc">(.*)</p>')
    items2 = re.findall(pattern2, html)
    for item in items2:
        yield {
            'content':item
        }

#爬取内容简介
def parse_one_page_recommend(html):
    # 匹配模式3：匹配推荐度
    pattern3 = re.compile('.*<span.*wr_bookList_item_reading_percent">(.*?)</span>.*')
    items3 = re.findall(pattern3, html)
    for item in items3:
        yield {
            'recommend':item
        }
def write_to_fire(content,name):
    with open(name,'a',encoding='utf-8') as f:
        print(type(json.dumps(content)))
        f.write(json.dumps(content,ensure_ascii=False)+'\n')

def main():
    url = 'https://weread.qq.com/web/category/all'
    html = get_one_page(url)
    parse_one_page(html)
    with open('result/resoure.csv', 'a', encoding='utf-8') as f:
        f.write('order URL Book_name author Reading_people\n')
        for item in parse_one_page(html):
            for i in item:
                f.write(i +' ')
            f.write('\n')
        # write_to_fire(item,r'result\resoure.csv')
    print('源数据获取成功！\n请求过于频繁，间隔 1 秒')
    # sleep(1)
    # for item in parse_one_page_recommend(html):
    #     print(item)
    #     write_to_fire(item,r'result\recommend.txt')
    # print('推荐指数获取成功！\n请求过于频繁，间隔 1 秒')
    # sleep(1)
    # for item in parse_one_page_content(html):
    #     print(item)
    #     write_to_fire(item,r'result\content.txt')
main()