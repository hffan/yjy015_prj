#--coding:utf-8--
# date:     2019-08-14
# function: read 5-minute averaged Real-time Integral Flux of High-energy Solar Protons 

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
    linesOfHeader=16
    for line in fh.readlines()[0:linesOfHeader]:
        print(line.strip())
    
    fh=open(fullpath)
    MissingVal=-1.00e+05
    for line in fh.readlines()[linesOfHeader:]:
        lineList=list(line.strip().split())
        YR=int(lineList[0])
        MO=int(lineList[1])
        DA=int(lineList[2])
        HH=int(lineList[3][0:2])
        MM=int(lineList[3][2:])
        Day=int(lineList[4])   
        Sec=int(lineList[5])
        
        # S_GT10MeV=int(lineList[6])
        # ProFlux_GT10MeV=float(lineList[7])if float(lineList[7])!=MissingVal else np.nan        
        # S_GT30MeV=int(lineList[8])
        # ProFlux_GT30MeV=float(lineList[9])if float(lineList[9])!=MissingVal else np.nan
        
        S_GT10MeV=int(lineList[6])
        ProFlux_GT10MeV=float(lineList[7])  
        S_GT30MeV=int(lineList[8])
        ProFlux_GT30MeV=float(lineList[9])  
        
        timeStamp=datetime.datetime(YR,MO,DA,HH,MM)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M')
        format='%s'+2*'%8d'+2*'%8d%10.2e'
        #print(format%(strTimeStamp,Day,Sec,S_GT10MeV,ProFlux_GT10MeV,S_GT30MeV,ProFlux_GT30MeV))
        
        # 绘图
        # data[timeStamp]={
            # 'ProFlux_GT10MeV':  ProFlux_GT10MeV,
            # 'ProFlux_GT30MeV': 	ProFlux_GT30MeV,
            # 'website':'SWPC',
            # 'category_abbr_en': 'SWPC_ace_sis5m'}
        
        # 入库
        data[strTimeStamp]={
            'ProFlux_GT10MeV':  ProFlux_GT10MeV,
            'ProFlux_GT30MeV': 	ProFlux_GT30MeV,
            'website':'SWPC',
            'category_abbr_en': 'SWPC_ace_sis5m'}

    return data
    
def plot_data(data):
    if data=={}:
        return
        
    timeStampArr=[]
    ProFlux_GT10MeVArr,ProFlux_GT30MeVArr=[],[]
    for key in data.keys():
        timeStamp=key
        ProFlux_GT10MeV=data[key]['ProFlux_GT10MeV']
        ProFlux_GT30MeV=data[key]['ProFlux_GT30MeV']
        
        timeStampArr.append(timeStamp)
        ProFlux_GT10MeVArr.append(ProFlux_GT10MeV)
        ProFlux_GT30MeVArr.append(ProFlux_GT30MeV)
        
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)	
    
    ax1 = plt.subplot(2,1,1)
    plt.plot(timeStampArr, ProFlux_GT10MeVArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=5)])
    plt.ylim()
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Flux > 10 MeV',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('5-minute averaged Real-time Integral Flux of High-energy Solar Protons',fontdict=font)
    plt.grid()
    
    ax2 = plt.subplot(2,1,2)
    plt.plot(timeStampArr, ProFlux_GT30MeVArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=5)])
    plt.ylim()
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Flux > 30 MeV',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()

    plt.savefig('ace_sis.png')
    plt.show()	

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='20190805_ace_sis_5m.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)
