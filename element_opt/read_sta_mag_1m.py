#--coding:utf-8--
# date:     2019-08-14
# function: read Real-time Interplanetary Magnetic Field Values sampled once per minute 

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
    for line in fh.readlines()[0:20]:
        print(line.strip())
    
    fh=open(fullpath)
    MissingVal=-999.9
    for line in fh.readlines()[20:]:
        lineList=list(line.strip().split())
        YR=int(lineList[0])
        MO=int(lineList[1])
        DA=int(lineList[2])
        HH=int(lineList[3][0:2])
        MM=int(lineList[3][2:])		
        Day=int(lineList[4])   
        Sec=int(lineList[5])
        S=int(lineList[6])
        
        # BR=float(lineList[7])if float(lineList[7])!=MissingVal else np.nan
        # BT=float(lineList[8])if float(lineList[8])!=MissingVal else np.nan
        # BN=float(lineList[9])if float(lineList[9])!=MissingVal else np.nan
        # Btotal=float(lineList[10])if float(lineList[10])!=MissingVal else np.nan
        # lat=float(lineList[11])if float(lineList[11])!=MissingVal else np.nan
        # lon=float(lineList[12])if float(lineList[12])!=MissingVal else np.nan

        BR=float(lineList[7])   
        BT=float(lineList[8])   
        BN=float(lineList[9])   
        Btotal=float(lineList[10])  
        lat=float(lineList[11]) 
        lon=float(lineList[12]) 
        
        timeStamp=datetime.datetime(YR,MO,DA,HH,MM)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M')
        format='%s'+3*'%6d'+6*'%10.2e'
        # print(format%(strTimeStamp,Day,Sec,S,BR,BT,BN,Btotal,lat,lon))
        
        # 绘图
        # data[timeStamp]={
            # 'S':  S,
            # 'BR': BR,
            # 'BT': BT,
            # 'BN': BN,
            # 'Btotal': Btotal,
            # 'Lat':lat,
            # 'Lon':lon,
            # 'website':'SWPC',
            # 'category_abbr_en': 'SWPC_STEA_mag',}
        
        # 入库
        data[strTimeStamp]={
            'S':  S,
            'BR': BR,
            'BT': BT,
            'BN': BN,
            'Btotal': Btotal,
            'Lat':lat,
            'Lon':lon,
            'website':'SWPC',
            'category_abbr_en': 'SWPC_STEA_mag',}
        
    return data
    
def plot_data(res):
    if data=={}:
        return
        
    timeStampArr=[]
    BxArr,ByArr,BzArr,BtArr,latArr,lonArr=[],[],[],[],[],[]
    for key in data.keys():
        timeStamp=key
        BR=data[key]['BR']
        Btotal=data[key]['Btotal']
        BN=data[key]['BN']
        Btotal=data[key]['Btotal']
        
        timeStampArr.append(timeStamp)
        BxArr.append(BR)
        ByArr.append(Btotal)
        BzArr.append(BN)
        BtArr.append(Btotal)
    
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)	
    
    ax1 = plt.subplot(4,1,1)
    plt.plot(timeStampArr, BxArr,'-.')
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-10,10])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('BR',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Real-time Interplanetary Magnetic Field Values sampled once per minute',fontdict=font)
    plt.grid()
    
    ax1 = plt.subplot(4,1,2)
    plt.plot(timeStampArr, ByArr,'-.')
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-10,10])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Btotal',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    ax1 = plt.subplot(4,1,3)
    plt.plot(timeStampArr, BzArr,'-.')
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-10,10])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('BN',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    ax1 = plt.subplot(4,1,4)
    plt.plot(timeStampArr, BtArr,'-.')
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([0,10])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Btotal',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
        
    plt.savefig('sta_mag.png')
    plt.show()	


if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='sta_mag_1m.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)