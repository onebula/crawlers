# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 15:45:19 2019

@author: Kuang
"""

import datetime
import re
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet

def is_weibo_page(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('href') and
        'page=' in tag.attrs['href']):
        return True
    return False

def extract_weibo_pages(tags):
    if type(tags) is not ResultSet:
        return None
    pages = []
    for tag in tags:
        pages.append(tag.attrs['href'].replace('amp;', ''))
    return pages

def is_weibo_topic(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('href') and 
        tag.has_attr('target')):
        topic = ''
        for t in tag.contents:
            if t.string:
                topic += t.string    
        if topic[0] == '#' and topic[-1] == '#':
            return True
    return False

def extract_weibo_topic(tag):
    if tag is None:
        return None, None    
    topic = ''
    for t in tag.contents:
        if t.string:
            topic += t.string
    return topic, tag.attrs['href'] 

def is_weibo_at(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('href') and 
        tag.has_attr('target') and
        tag.string and
        '@' in tag.string):
        return True
    return False

def extract_weibo_at(tag):
    if tag is None:
        return None, None
    return tag.string, tag.attrs['href']

def is_weibo_content(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'p' and
        tag.has_attr('class') and 
        tag.attrs['class'] == ['txt'] and
        tag.has_attr('node-type') and
        tag.attrs['node-type'] == "feed_list_content" and
        tag.has_attr('nick-name')):
        return True
    return False
    
def extract_weibo_author_text(tag):
    if type(tag) is not Tag:
        return None, None
    if tag is None:
        return None, None
    text = ''
    for t in tag.contents[1:]:
        if t.string:
            text += t.string
    author = tag.attrs['nick-name']
    return author, text

def extract_photo_author(text):
    photo_author = re.findall('[（](.*?)[）]', text)
    if photo_author:
        return photo_author[-1]
    else:
        return None
    
def is_weibo_repost(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('action-data') and 
        tag.has_attr('action-type') and
        tag.has_attr('href') and
        tag.has_attr('suda-data') and
        tag.string and
        '转发' in tag.string):
        return True
    return False

def extract_weibo_repost(tag):
    if tag is None:
        return 0
    num = tag.string.split(' ')[-1]
    if len(num) != 0:
        return int(num)
    return 0

def is_weibo_comment(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('action-data') and 
        tag.has_attr('action-type') and
        tag.has_attr('href') and
        tag.has_attr('suda-data') and
        tag.string and
        '评论' in tag.string):
        return True
    return False

def extract_weibo_comment(tag):
    if tag is None:
        return 0  
    num = tag.string.split(' ')[-1]
    if len(num) != 0:
        return int(num)
    return 0
    
def is_weibo_like(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and 
        tag.has_attr('action-data') and 
        tag.has_attr('action-type') and
        tag.has_attr('href') and
        tag.has_attr('suda-data') and
        tag.has_attr('title') and
        '赞' in tag.attrs['title']):
        return True
    return False

def extract_weibo_like(tag):
    if tag is None:
        return 0
    num = tag.find_all('em')[0].string
    if num:
        return int(num)
    return 0

def is_weibo_source(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'a' and
        tag.has_attr('href') and
        tag.has_attr('target') and
        tag.has_attr('suda-data') and
        tag.string and
        ('分钟前' in tag.string or 
         '秒前' in tag.string or
         ('月' in tag.string and '日' in tag.string) or
         ('今天' in tag.string and ':' in tag.string)) and
        'ul' != tag.parent.previous_sibling.previous_sibling.name):
        return True
    return False

def extract_weibo_source(tag):
    if tag is None:
        return None, None
    timestr = tag.string.replace(' ', '').replace('\n', '')
    if tag.next_sibling.next_sibling:
        source = tag.next_sibling.next_sibling.string
    else:
        source = None
    return timestr, source

def is_weibo_pic(tag):
    if type(tag) is not Tag:
        return False
    if (tag.name == 'img' and
        tag.has_attr('action-data') and
        tag.has_attr('action-type') and
        tag.has_attr('src') and
        tag.has_attr('suda-data')):
        return True
    return False

def extract_weibo_pics(tags):
    if type(tags) is not ResultSet:
        return None
    pics = []
    for tag in tags:
        pics.append(tag.attrs['src'])
    return pics

def process_pages(soup):
    # 整理页面信息
    pagelist = soup.find('span', class_='list')
    pages = extract_weibo_pages(pagelist.find_all(is_weibo_page))
    return pages    

def process_search_page(soup):
    # 整理内容信息
    weibos = soup.find_all(is_weibo_content)
    wbs = [WeiBo() for i in range(len(weibos))]
    for i, weibo in enumerate(weibos):
        wbs[i].author, wbs[i].text = extract_weibo_author_text(weibo)
        wbs[i].topic, wbs[i].topic_dir = extract_weibo_topic(weibo.find(is_weibo_topic))
        wbs[i].at, wbs[i].at_dir = extract_weibo_at(weibo.find(is_weibo_at))
        if wbs[i].at is None:
            wbs[i].at = extract_photo_author(wbs[i].text)
        for node in weibo.next_siblings:
            if type(node) is Tag:
                weibo_pics = node.find_all(is_weibo_pic)
                if len(weibo_pics) > 0:
                    wbs[i].pics = extract_weibo_pics(weibo_pics)
                    break
    
    # 整理指标信息
    kpis = soup.find_all('div', class_="card-act")
    if len(kpis) != len(wbs):
        print('Fatal Error! kpis')
        return
    for i, kpi in enumerate(kpis):
        wbs[i].repost_n = extract_weibo_repost(kpi.find(is_weibo_repost))
        wbs[i].comment_n = extract_weibo_comment(kpi.find(is_weibo_comment))
        wbs[i].like_n = extract_weibo_like(kpi.find(is_weibo_like))
    
    # 整理时间和来源信息
    sources = soup.find_all(is_weibo_source)
    if len(sources) != len(wbs):
        print('Fatal Error! sources')
        return
    for i, source in enumerate(sources):
        wbs[i].time, wbs[i].source = extract_weibo_source(source)
    
    return wbs

class WeiBo:
    def __init__(self):
        self.author = None
        self.topic = None
        self.topic_dir = None
        self.text = None
        self.at = None
        self.at_dir = None
        self.pics = None
        self.repost_n = 0
        self.comment_n = 0
        self.like_n = 0
        self.time = None
        self.source = None
        self.record_time = datetime.datetime.now()

def crawler_search_page(keyword, vip=1, haspic=1, hot=0):
    '''
    爬取微博关键词搜索页面所展示的所有微博
    默认过滤条件：认证用户vip=1 + 图片haspic=1
    '''
    wb_list = []
    payload = {'q': keyword, 'Refer': 'g'}
    if vip == 1:
        payload['vip'] = str(vip)
    if haspic == 1:
        payload['haspic'] = str(haspic)
    if hot == 1:
	    payload['xsort'] = 'hot'
    print(payload)
    url = 'https://s.weibo.com/weibo'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
               'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Cache-Control': 'max-age=0'}
    r = requests.get(url, headers=headers, params=payload)
    print(r.url)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    pages = process_pages(soup)
    soups = []
    for i, page in enumerate(pages):
        print(i)
        pageurl = 'https://s.weibo.com' + page
        html = requests.get(pageurl, headers=headers).text
        soup = BeautifulSoup(html, 'html.parser')
        wbs = process_search_page(soup)
        print('len = ' + str(len(wbs)))
        # 未登陆状态下数量与登陆状态下数量可能不同
        wb_list += wbs
        soups.append(soup)
    return wb_list, soups

if __name__ == "__main__":
    
    wb_list, soups = crawler_search_page('#大美北大#')
    #wb_list, soups = crawler_search_page('#看不见的武大#')
    #wb_list, soups = crawler_search_page('#向佐叫郭碧婷老婆#')
    #wb_list, soups = crawler_search_page('#向佐叫郭碧婷老婆#', 0, 0)
    #wb_list, soups = crawler_search_page('#苹果Siri项目主管被撤职#', vip=1, haspic=0)
    #wb_list, soups = crawler_search_page('#毕业后同学差距有多大#', vip=1, haspic=0)                                         
                                         
                                          
    import pandas as pd
    df = pd.DataFrame({'text': [wb.text for wb in wb_list]})
    df['text'].to_csv('text.txt', header = False, index = False)
    
    df1 = pd.DataFrame({'names': list(set([wb.at.replace('@', '').replace('摄影', '').replace('：', '')
                                for wb in wb_list if (wb.at and len(wb.at.replace('@', '').replace('摄影', '').replace('：', ''))>0)]))})
    df1['names'].to_csv('names.txt', header = False, index = False)
    
    corpus = []
    for wb in wb_list:
        #if wb.at != '@小潭竹影':
        #    continue
        a1 = wb.text.find('(')
        a2 = wb.text.find('（')
        a3 = wb.text.find('摄影')
        no_at = wb.text
        if a1 >= 0:
            no_at = no_at[0:a1]
        if a2 >= 0:
            no_at = no_at[0:a2]
        if a3 >= 0:
            no_at = no_at[0:a3]
        corpus.append(no_at)
    df2 = pd.DataFrame({'corpus': corpus})
    df2['corpus'].to_csv('corpus.txt', header = False, index = False)
        