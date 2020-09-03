#--coding:utf-8--
# date:     2019-08-14
# function: read Real-time Bulk Paramters of the Solar Wind Plasma

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
    linesOfHeader=18
    for line in fh.readlines()[0:linesOfHeader]:
        print(line.strip())
    
    fh=open(fullpath)

    MissingVal1=-9999.9
    MissingVal2=-1.00e+05
    for line in fh.readlines()[linesOfHeader:]:
        lineList=list(line.strip().split())
        YR=int(lineList[0])
        MO=int(lineList[1])
        DA=int(lineList[2])
        HH=int(lineList[3][0:2])
        MM=int(lineList[3][2:])		
        Day=int(lineList[4])   
        Sec=int(lineList[5])
        S=int(lineList[6])
        
        # Density=float(lineList[7])  if float(lineList[7])!=MissingVal1 else np.nan
        # Speed=float(lineList[8])    if float(lineList[8])!=MissingVal1 else np.nan
        # Temp=float(lineList[9])     if float(lineList[9])!=MissingVal2 else np.nan

        Density=float(lineList[7])  
        Speed=float(lineList[8])    
        Temp=float(lineList[9])     
        
        timeStamp=datetime.datetime(YR,MO,DA,HH,MM)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M')
        format='%s'+3*'%8d'+3*'%10.2e'
        #print(format%(strTimeStamp,Day,Sec,S,Density,Speed,Temp))

        # 绘图
        # data[timeStamp]={
            # 'S':  S,
            # 'Density': Density,
            # 'Speed': Speed,
            # 'Temp': Temp,
            # 'website':'SWPC',
            # 'category_abbr_en': 'SWPC_STEA_plastic',}
        
        # 入库
        data[strTimeStamp]={
            'S':  S,
            'Density': Density,
            'Speed': Speed,
            'Temp': Temp,
            'website':'SWPC',
            'category_abbr_en': 'SWPC_STEA_plastic',}
        
    return data
    
def plot_data(res):
    if data=={}:
        return
        
    timeStampArr=[]
    DensityArr,SpeedArr,TempArr=[],[],[]
    for key in data.keys():
        timeStamp=key
        Density=data[key]['Density']
        Speed=data[key]['Speed']
        Temp=data[key]['Temp']
        
        timeStampArr.append(timeStamp)
        DensityArr.append(Density)
        SpeedArr.append(Speed)
        TempArr.append(Temp)
    
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)	
    
    ax1 = plt.subplot(3,1,1)
    plt.plot(timeStampArr, DensityArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim()
    # plt.xlabel('UT',fontdict=font)
    plt.ylabel('Density',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Real-time Bulk Paramters of the Solar Wind Plasma',fontdict=font)
    plt.grid()
    
    ax2 = plt.subplot(3,1,2)
    plt.plot(timeStampArr, SpeedArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim()
    # plt.xlabel('UT',fontdict=font)
    plt.ylabel('Speed',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    ax2 = plt.subplot(3,1,3)
    plt.plot(timeStampArr, TempArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim()
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Temperature',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()

    plt.savefig('sta_plastic.png')
    plt.show()	

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='sta_plastic_1m.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)
