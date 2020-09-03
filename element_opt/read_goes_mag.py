#--coding:utf-8--
# date:     2020-05-12
# function: read 1-minute GOES-16 magnetometers data,json file

import os
import sys
import time
import calendar
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'


def read_data(fullpath):
    data={}
    if not os.path.exists(fullpath):
        return data
        
    fh = open(fullpath,encoding='utf-8')
    content = fh.read() 		#使用loads()方法需要先读文件
    lst = json.loads(content)	#loads()返回结果为list
    num=len(lst)				#记录个数
    
    # 字典内容
    # {"time_tag": "2020-05-10T02:40:00Z", 
    #  "satellite": 16, 
    #  "He": 40.73655319213867, 
    #  "Hp": 92.05882263183594, 
    #  "Hn": -3.0874006748199463, 
    #  "total": 100.71661376953125, 
    #  "arcjet_flag": false}
    
    for rec in lst:
        time_tag=rec["time_tag"]
        timeStamp=datetime.datetime.strptime(time_tag,'%Y-%m-%dT%H:%M:%SZ')
        str_timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        
        satellite='GOES'+str(rec["satellite"])
        Hp=rec["Hp"]
        He=rec["He"]
        Hn=rec["Hn"]
        TotalField=rec["total"]
        arcjet_flag=rec["arcjet_flag"]
        
        # 绘图
        # data[timeStamp]={
            # 'Hp':Hp,
            # 'He':He,
            # 'Hn':Hn,
            # 'TotalField':TotalField,
            # 'satellite':satellite,
            # 'time_resolution':1,
            # 'website':'SWPC',
            # 'category_abbr_en':'SWPC_GOES_mag1m'}
         
        # 入库
        data[str_timeStamp]={
            'Hp':Hp,
            'He':He,
            'Hn':Hn,
            'TotalField':TotalField,
            'satellite':satellite,
            'time_resolution':1,
            'website':'SWPC',
            'category_abbr_en':'SWPC_GOES_mag1m'}
        
    return data
    
def plot_data(data,fullpath):
    if data=={}:
        return
        
    timeStampArr=[]
    HpArr,HeArr,HnArr,TotalFieldArr=[],[],[],[]
    for key in data.keys():
        timeStamp=key
        Hp=data[key]['Hp']
        He=data[key]['He']
        Hn=data[key]['Hn']
        TotalField=data[key]['TotalField']
        
        timeStampArr.append(timeStamp)
        HpArr.append(Hp)
        HeArr.append(He)
        HnArr.append(Hn)
        TotalFieldArr.append(TotalField)
    
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)	
    
    ax1 = plt.subplot(1,1,1)
    h1,=plt.plot(timeStampArr, HpArr)
    h2,=plt.plot(timeStampArr, HeArr)
    h3,=plt.plot(timeStampArr, HnArr)
    h4,=plt.plot(timeStampArr, TotalFieldArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+(timeStampArr[1]-timeStampArr[0])])
    plt.ylim([-50,200])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Geomagnetic Components',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels]
    plt.legend(handles = [h1,h2,h3,h4],\
        labels = ['Hp','He','Hn','TotalField'],\
        loc = 'best',\
        prop={'family':'Times New Roman','size':10})
    plt.title('1-minute GOES Geomagnetic Components and Total Field',fontdict=font)
    plt.grid()
    
    savepath=fullpath.replace('.json','.png')
    plt.savefig(savepath)
    plt.show()	
    
if __name__ == '__main__':
    fullpath='magnetometers-1-day.json'
    data=read_data(fullpath)
    plot_data(data,fullpath)
    