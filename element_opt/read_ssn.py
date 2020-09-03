#--coding:utf-8--
# date:     2019-08-09
# function: read Daily total sunspot number

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
    for line in fh.readlines():
        lineList=list(line.strip().split())
        year=int(lineList[0])
        month=int(lineList[1])
        day=int(lineList[2])
        dsn=int(lineList[4])
        sd=float(lineList[5])
        num_obs=int(lineList[6])
        
        timeStamp=datetime.datetime(year,month,day)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        
        # # 绘图
        # data[timeStamp]={
            # 'dsn':dsn,
            # 'sd':sd,
            # 'num_obs':num_obs,
            # 'website':'SIDC',
            # 'category_abbr_en':'SIDC_SN_dat'}
        
        # 入库
        data[strTimeStamp]={
            'sn':dsn,
            'std':sd,
            'num_obs':num_obs,
            'website':'SIDC',
            'category_abbr_en':'SIDC_SN_dat'}
        
    return data
        
def plot_data(data):
    if data=={}:
        return

    timeStampArr,dsnArr,sdArr,num_osbsArr=[],[],[],[]
    for key in data.keys():
        timeStamp=key
        dsn=data[key]['dsn']
        sd=data[key]['sd']
        num_obs=data[key]['num_obs']
    
        timeStampArr.append(timeStamp)
        dsnArr.append(dsn)
        sdArr.append(sd)
        num_osbsArr.append(num_obs)
        
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
    ax1 = plt.subplot(1,1,1)
    h1,=plt.plot(timeStampArr[-365*22:-1:1], dsnArr[-365*22:-1:1],linewidth=0.5)
    plt.xlim([timeStampArr[-365*22],timeStampArr[-1]])
    plt.ylim([0,400])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Sunspot Number',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Daily sunspot number',fontdict=fontTitle)
    
    ax2 = ax1.twinx()  # this is the important function
    h2,=plt.plot(timeStampArr[-365*22:-1:1], num_osbsArr[-365*22:-1:1], '-.r',linewidth=0.5)
    plt.xlim([timeStampArr[-365*22],timeStampArr[-1]])
    plt.ylim([0,60])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Number of observations',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Daily sunspot number',fontdict=fontTitle)
    plt.grid()
    
    plt.savefig('sn.png')
    plt.show()
    
if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='SN_d_tot_V2.0.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)