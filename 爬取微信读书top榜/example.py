# 爬取微信阅读top总榜
import requests
import re
import csv
url = "https://weread.qq.com/web/shelf"
res = requests.get(url)
print(res)
res.encoding = 'utf-8'
# print(res.text)

obj = re.compile(r'<p class="wr_bookList_item_index">(?P<index>\d+)</p>'
                 r'.*?<p class="wr_bookList_item_title">(?P<name>.*?)</p>'
                 r'<p class="wr_bookList_item_author"><.*?>(?P<author>.*?)</a>.*?<p class="wr_bookList_item_desc">('
                 r'?P<description>.*?)</p>', re.S)

# obj = re.compile(r'<p class="wr_bookList_item_index">(?P<index>.*?)</p>', re.S)
result = obj.finditer(res.text)
books = []
for item in result:
    dic = item.groupdict()
    dic['作者'] = dic.pop('author')
    dic['排名'] = dic.pop('index')
    dic['书名'] = dic.pop('name')
    dic['描述'] = dic.pop('description')
    books.append(dic)
    print(dic)

header = ["排名", "作者", "书名", "描述"]
# newline是数据之间不加空行
with open('weixingRead.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=header)  # 提前预览列名
    writer.writeheader()
    writer.writerows(books)


