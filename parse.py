# coding = utf-8
import time as _time
import datetime
import re
import copy
import logging
import os

import requests
import bs4
import pymongo

#os.chdir(r'C:\Users\27455\source\repos\Tieba Parser')

num_mode = re.compile(r'\d+')
myclient = pymongo.MongoClient('mongodb://localhost:27017/')
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename='log\\{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')), datefmt=DATE_FORMAT,
                    format=LOG_FORMAT, level=logging.INFO)

keys = ['user_name', 'user_id', 'content', 'time', 'is_comment']

def get_attrs(tag):
    attrs = tag.attrs['data-field'].replace('null', 'None').replace('false', 'False').replace('true', 'True')
    return eval(attrs)

class SubLevel(object):
    def __init__(self, tag):
        data = get_attrs(tag)
        self.name = data['user_name']
        timestring = tag.find_all('span')[-1].contents[0]
        self.time = datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M')
        self.content = tag.find_all('', attrs={'class':'lzl_content_main'})[0].contents[0].strip()

class Comment(object):
    def __init__(self, tag, tid=None):
        t = tag.find('', attrs={'class':'j_lzl_r p_reply'})
        self.comment = list()
        self.tid = tid
        if t is None:
            self.comment_num = 0
        else:
            data = get_attrs(t)
            self.pid = data['pid']
            self.comment_num = data['total_num']
        if isinstance(self.comment_num, int) and self.comment_num > 0:
            self.retrieve_comment_content()

    def retrieve_comment_content(self):
        url = 'https://tieba.baidu.com/p/comment?tid={}&pid={}&pn={}'
        pagenum = self.comment_num // 10 + 1
        for i in range(1, pagenum + 1):
            while True:
                try:
                    req = requests.get(url.format(self.tid, self.pid, i))
                    break
                except Exception:
                    logging.warn('Connection Failed, retrying ...')
                    _time.sleep(5)
            soup = bs4.BeautifulSoup(req.content, 'html5lib')
            comment_list = soup.find_all('li')
            for cmt in comment_list:
                if 'lzl_single_post' in cmt.attrs['class']:
                    self.comment.append(SubLevel(cmt))

def parse(url, db, start_page=1):
    tid = int(re.findall(num_mode, url)[0])
    collect = db[str(tid)]
    url += '?pn={}'
    count = start_page
    while 1:
        while True:
            try:
                req = requests.get(url.format(count))
                break
            except Exception:
                logging.warn('Connection Failed, retrying...')
                _time.sleep(5)
        soup = bs4.BeautifulSoup(req.content)
        body = soup.find('body')
        data = body.find_all('div')[1].find('div')
        pages = data.find('', attrs={'class':'l_posts_num'}).find_all('a')
        max_pagenum = int(re.findall(num_mode, pages[-1].attrs['href'])[1])
        content = data.find_all('div')[7].find('div').find('div', id='pb_content')
        auth = soup.find_all('div', attrs={'class':'d_author'})
        user_id = list()
        user_name = list()
        content = list()
        for i in auth:
            user_name.append(i.find('img').attrs['username'])
            d2 = get_attrs(i.find('', attrs={'class':'d_name'}))
            user_id.append(d2['user_id'])
        postlist = soup.find_all('', attrs={'class':'d_post_content j_d_post_content'})
        content = [i.contents[0].strip().encode('UTF-8','ignore').decode('UTF-8') for i in postlist]
        lzl = soup.find_all('', attrs={'class':'core_reply j_lzl_wrapper'})
        timestring = [i.find_all('', attrs={'class':'tail-info'})[-1].contents[0] for i in lzl]
        time =  [datetime.datetime.strptime(i, '%Y-%m-%d %H:%M').timestamp() for i in timestring]
        is_comment = [False for i in content]
        comment_decoded = [Comment(i, tid=tid) for i in lzl]
        fin = list()
        for cmt in comment_decoded:
            fin = fin + cmt.comment
        user_id_cmt = [None for i in fin]
        user_name_cmt = [i.name for i in fin]
        content_cmt = [i.content.encode('UTF-8','ignore').decode('UTF-8') for i in fin]
        time_cmt = [i.time.timestamp() for i in fin]
        is_comment_cmt = [True for i in fin]

        result = zip([*user_name, *user_name_cmt], [*user_id, *user_id_cmt], [*content, *content_cmt], [*time, *time_cmt], [*is_comment, *is_comment_cmt])
        for r in result:
            collect.insert(dict(zip(keys, r)))
        logging.info('Parse complete. {}'.format(url.format(count)))
        if count >= max_pagenum:
            break
        count += 1

if __name__ == '__main__':
    url = 'https://tieba.baidu.com/p/6215376084'
    db = myclient['tieba_parser']
    try:
        parse(url, db)
    except Exception as e:
        import traceback
        logging.warn('Error occured: {}'.format(traceback.format_exc()))