#--coding:utf-8--
# date:     2019-08-09
# function: read the Solar Flux Data

import os
import sys
import time
import calendar
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'

def read_data(fullpath):
    data={}
    if not os.path.exists(fullpath):
        return data

    fh=open(fullpath)
    # skip first two line
    Header=fh.readline()
    Header=fh.readline()
    
    line = fh.readline()
    while line:
        listLine=line.strip().split()
        date=listLine[0]   
        time=listLine[1] 
        julian=float(listLine[2])
        carrington=float(listLine[3])
        obsflux=float(listLine[4])
        adjflux=float(listLine[5])
        ursiflux=float(listLine[6])
        
        timeStamp=datetime.datetime.strptime(date+time,'%Y%m%d%H%M%S')
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        # print('%s   obsflux=%8.2f   adjflux=%8.2f   ursi=%8.2f'%(strTimeStamp,obsflux,adjflux,ursiflux))
        
        # 读取下一行
        line = fh.readline()
        
        # 绘图
        # data[timeStamp]={
            # 'julian':julian,
            # 'carrington':carrington,
            # 'obsflux':obsflux,
            # 'adjflux':adjflux,
            # 'ursiflux':ursiflux,
            # 'website':'NRCAN',
            # 'category_abbr_en':'NRCAN_F107_txt'}
        
        # 入库
        data[strTimeStamp]={
            'julian':julian,
            'carrington':carrington,
            'obsflux':obsflux,
            'adjflux':adjflux,
            'ursiflux':ursiflux,
            'website':'NRCAN',
            'category_abbr_en':'NRCAN_F107_txt'}
        
    return data
    
def plot_data(data):
    if data=={}:
        return 
    
    timeStampArr,obsfluxArr,adjfluxArr,ursifluxArr=[],[],[],[]
    for key in data.keys():
        timeStamp=key
        obsflux=data[key]['obsflux']
        adjflux=data[key]['adjflux']
        ursiflux=data[key]['ursiflux']
        
        timeStampArr.append(timeStamp)	
        obsfluxArr.append(obsflux)
        adjfluxArr.append(adjflux)
        ursifluxArr.append(ursiflux)
            
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    fontTitle={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':14
        }

    plt.figure(figsize=(8, 6), dpi=150)	
    ax = plt.subplot(1,1,1)
    h1,=plt.plot(timeStampArr, obsfluxArr)
    h2,=plt.plot(timeStampArr, adjfluxArr)
    h3,=plt.plot(timeStampArr, ursifluxArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]])
    plt.ylim([0,1000])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('flux',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax.get_xticklabels() + ax.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('10.7cm Solar Flux',fontdict=fontTitle)
    plt.legend(handles = [h1,h2,h3,],\
        labels = ['The observed flux', 'The adjusted flux','The Series D flux'],\
        loc = 'best',\
        prop={'family':'Times New Roman','size':12})
    plt.grid()
    plt.savefig('f107.png')
    plt.show()
    
if __name__ == '__main__':
    # 1，获取数据文件全路径
    cwd = os.getcwd()
    filename='fluxtable.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)