import pandas as pd
import matplotlib
matplotlib.rc('font', family='Arial')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import numpy as np
import time
import datetime
from collections import Counter
import matplotlib.dates as mdates
import pymongo

tid = '6215376084'

myclient = pymongo.MongoClient('mongodb://localhost:27017/')
db = myclient['tieba_parser']
col = db[tid]

df = pd.DataFrame(col.find())
_time = df['time'].values
loct = [time.localtime(i) for i in _time]
dtime = np.array([datetime.datetime(*s[0:6]) for s in loct]).astype(np.datetime64)
'''
hist = np.histogram(t, bins=(t.max() - t.min()) // 3600)
loct = [time.localtime(i) for i in hist[1]]
dtime = np.array([datetime.datetime(*s[0:6]) for s in loct]).astype(np.datetime64)
'''
out_x = np.arange(dtime.min(), dtime.max(), np.timedelta64(1, 'm'))
out_y = np.zeros(out_x.shape)
t_c = Counter(dtime)
q = pd.DataFrame(t_c.most_common())
new = q.sort_values(0)
newt = new[0].values
newc = new[1].values
for idx, var in zip(newt, newc):
    pos = np.where(idx == out_x)[0]
    out_y[pos] = var

# calculate hourly sum
first_minute = out_x[0].astype(datetime.datetime)
begin_offset = 60 - first_minute.minute
end_offset = (out_x.shape[0] - begin_offset) % 60
main = out_y[begin_offset:-end_offset]
main = main.reshape(main.shape[0] // 60, 60)
hour_sum = main.sum(axis=1)
total = np.array([np.sum(out_y[:begin_offset])] + hour_sum.tolist() + [np.sum(out_y[-end_offset:])])
plot_area = np.where(total > 5)[0][-1]
first_time = first_minute - datetime.timedelta(minutes=first_minute.minute)
x = ([first_time] + out_x[begin_offset::60].tolist())[:plot_area]
y = total[:plot_area]

#x = np.load('D:\\tbx.npy')
#y = np.load('D:\\tby.npy')

plt.figure(figsize=(11, 5), dpi=200)
plt.plot(x, y)
ax = plt.gca()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.gcf().autofmt_xdate()
plt.xlim(np.min(x), np.max(x))
plt.ylim(0, None)
plt.title('TID {}'.format(tid))
plt.ylabel('Comments per hour')
plt.savefig('D:\\贴吧数据统计\\{}.png'.format(tid), bbox_inches='tight')

name = df['user_name'].values
c = Counter(name)
for idx, i in enumerate(c.most_common(60)):
    print(str(idx + 1) + '. ' + ' '.join([str(j) for j in i]))

print(Counter(dtime).most_common(1))
print(y.max())
print(x[np.where(y==y.max())[0][0]])