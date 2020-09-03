#--coding:utf-8--
# date:     2019-08-12
# function: read Daily Geomagnetic Data

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

def geomag_strom(P):    
    # 功能：地磁暴事件等级
    # 输入：地磁Kp指数
    # 输出：地磁暴等级，共4级别
    
    levels={
        'L1':'小',
        'L2':'中等',
        'L3':'大',
        'L4':'特大',
        'L5':'超大'}
    
    measures={
        'L1':5,
        'L2':6,
        'L3':7,
        'L4':8,
        'L5':9}
        
    descrips={
        'L1':'',
        'L2':'',
        'L3':'',
        'L4':'强',
        'L5':'超强'}
    
    descrip=''
    level=''
    for key in descrips:
        if P>=measures[key]:
            descrip=descrips[key]
            level=levels[key]
    return level,descrip
    
def read_data(fullpath):
    data_kp,data_Ap={},{}
    if not os.path.exists(fullpath):
        return data_kp,data_Ap
        
    fh=open(fullpath)
    # for line in fh.readlines()[0:12]:
        # print(line.strip())
        
    fh=open(fullpath)
    data_kp,data_ap={},{}
    for line in fh.readlines()[12:]:
        # print(line)
        line=line.replace('-',' -')
        lineList=list(line.strip().split())
        lineArr=list(map(int,lineList))
        year,month,day=lineArr[0],lineArr[1],lineArr[2]
        
         # （1）Kp指数
        timeStampArr=[]
        KMidLatArr,KHighLatArr,KpArr=[],[],[]
        for id in range(8):
           
            hour=id*3
            dt=datetime.timedelta(hours=3)
            
            timeStamp=datetime.datetime(year,month,day,hour)+dt
            strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M:%S')
            timeStampArr.append(timeStamp)
            KMidLat=lineArr[4+id]
            KHighLat=lineArr[13+id]
            Kp=lineArr[22+id]
            level,descrip=geomag_strom(Kp)
            # print('%s %8d %8d %8d'%(strTimeStamp,KMidLat,KHighLat,Kp))
            
            # 剔除未来时刻的缺省值
            if  timeStamp>datetime.datetime.utcnow():
                continue
            if Kp==-1:
                continue

                
            # # 绘图
            # data_kp[timeStamp]={
                # 'Kp': Kp,
                # 'KMidLat': KMidLat,
                # 'KHighLat': KHighLat,
                # 'level':level,
                # 'descrip':descrip,
                # 'website':'SWPC',
                # 'category_abbr_en': 'SWPC_latest_DGD',}
            
            # 入库
            data_kp[strTimeStamp]={
                'Kp': Kp,
                'KMidLat': KMidLat,
                'KHighLat': KHighLat,
                'level':level,
                'descrip':descrip,
                'website':'SWPC',
                'category_abbr_en': 'SWPC_latest_DGD',}
                
            # KMidLatArr.append(KMidLat)
            # KHighLatArr.append(KHighLat)
            # KpArr.append(Kp)
            
        # plot_data(data=[timeStampArr,KpArr])
        
        
        

         # （2）Ap指数
        timeStamp=datetime.datetime(year,month,day)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        A_midLat=lineArr[3]
        A_highLat=lineArr[12]
        Ap=lineArr[21]
        # print('%s %8d %8d %8d'%(strTimeStamp,A_midLat,A_highLat,Ap))
        
        if Ap==-1:
            continue        
        # 剔除未来时刻的缺省值
        if  timeStamp>datetime.datetime.utcnow():
            continue
            
        # 绘图       
        # data_Ap[timeStamp]={
            # 'Ap': Ap,
            # 'A_midLat': A_midLat,
            # 'A_highLat': A_highLat,
            # 'website':'SWPC',
            # 'category_abbr_en': 'SWPC_latest_DGD'}
        
        # 入库
        data_Ap[strTimeStamp]={
            'Ap': Ap,
            'A_midLat': A_midLat,
            'A_highLat': A_highLat,
            'website':'SWPC',
            'category_abbr_en': 'SWPC_latest_DGD'}

    # for key in data_kp.keys():
        # print(key,data_kp[key])
        
    return data_kp,data_Ap
        
        
def plot_data(data):
    print(data)
    timeStampArr=data[0]
    KpArr=data[1]
            
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
    
    plt.figure(figsize=(8, 6), dpi=150)	
    ax = plt.subplot(1,1,1)
    facecolors=['green','green','green','green','yellow','red','red','red','red','red']
    for id in range(len(KpArr)):
        plt.bar(timeStampArr[id], KpArr[id], width = 0.1,facecolor=facecolors[KpArr[id]])
    plt.xlim([timeStampArr[0],timeStampArr[-1]])
    plt.ylim([0,9])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('KpArr index',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax.get_xticklabels() + ax.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('Geomagnetic Planetary Indices',fontdict=font)
    plt.grid(axis='y')
    plt.ion()
    
    plt.pause(0.1)
    plt.savefig('DGD.png')
    plt.close()	

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    fullpath='DGD.txt'
    fullpath=cwd+'/'+fullpath
    
    # 2，读取数据
    data_kp,data_Ap=read_data(fullpath)
