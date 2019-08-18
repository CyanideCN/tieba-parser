import re
import pandas as pd
from wordcloud import WordCloud
from collections import Counter

zhongwen_pat = re.compile(r'^[\u4e00-\u9fa5a-zA-Z]+$')

df = pd.read_json(r'D:\贴吧数据统计\6041584268.json', lines=True, encoding='utf-8')
content = ''.join(df.content.values).replace('回复', '')
ctr = Counter(df.user_name)
stp = {i[0] for i in ctr.most_common()}
for i in stp:
    content = content.replace(i, '')

c = WordCloud(font_path=r"C:\Windows\Fonts\Deng.ttf", width=1500, height=1200)
c.generate(content)
c.to_file('D:\\123.png')

import numpy as np
import re
f = open(r'C:\Users\27455\Documents\Tencent Files\274555447\FileRecv\SURF_CLI_CHN_PRE_MON_GRID_0.5-196208.txt')
ctt = f.readlines()
num_mode = re.compile(r'(\-?[1-9]\d*\.?\d*)|(\-?0\.\d*[1-9])')
out = list()
for i in ctt[6:]:
    res = re.findall(num_mode, i)
    out.append([j for i in res for j in i if j])
q = np.array(out, float)
data = np.ma.array(q, mask=q==-9999)