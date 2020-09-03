#--coding:utf-8--
# date:     2019-08-14
# function: read Aurora Hemispheric Power Tabular Values

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

    MissingVal='n/a'
    for line in fh.readlines()[linesOfHeader:]:
        lineList=list(line.strip().split())
        strTimeStamp=lineList[0]+' '+lineList[1]
        timeStamp=datetime.datetime.strptime(strTimeStamp,'%Y-%m-%d %H:%M')
        NorthHPI=int(lineList[2])if lineList[2]!=MissingVal else np.nan
        SouthHPI=int(lineList[3])if lineList[3]!=MissingVal else np.nan
        
        # format='%s'+2*'%8.0f' 
        #print(format%(strTimeStamp,NorthHPI,SouthHPI))
        
        # 绘图
        # data[timeStamp]={
            # 'NorthHPI':NorthHPI,
            # 'SouthHPI':SouthHPI,
            # 'website':'SWPC',
            # 'category_abbr_en':'SWPC_Aurora_hpi'}
        
        # 入库
        data[strTimeStamp]={
            'NorthHPI':NorthHPI,
            'SouthHPI':SouthHPI,
            'website':'SWPC',
            'category_abbr_en':'SWPC_Aurora_hpi'}
            
    return data
    
def plot_data(data):
    if data=={}:
        return 
        
    timeStampArr=[]
    NorthHPIArr,SouthHPIArr=[],[]
    for key in data.keys():
        timeStamp=key
        NorthHPI=data[key]['NorthHPI']
        SouthHPI=data[key]['SouthHPI']
        timeStampArr.append(timeStamp)
        NorthHPIArr.append(NorthHPI)
        SouthHPIArr.append(SouthHPI)
        
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=128)	
    
    ax1 = plt.subplot(2,1,1)
    plt.plot(timeStampArr, NorthHPIArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=5)])
    plt.ylim()
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('NorthHPI',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Aurora Hemispheric Power',fontdict=font)
    plt.grid()
    
    ax2 = plt.subplot(2,1,2)
    plt.plot(timeStampArr, SouthHPIArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=5)])
    plt.ylim()
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('SouthHPI',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    plt.savefig('hpi.png')
    plt.show()	

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='swpc_aurora_power_20190805.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)
