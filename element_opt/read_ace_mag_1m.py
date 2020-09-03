#--coding:utf-8--
# date:     2019-08-14
# function: read 1-minute averaged Real-time Interplanetary Magnetic Field Values 

import os
import sys
import time
import calendar
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from spacepy.coordinates import Coords
from spacepy.time import Ticktock

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'

def GSM2GSE(year,month,day,hour,min,sec,GSM_XYZ):
    # 功能：GSM坐标系->GSE坐标系
    coord = Coords(GSM_XYZ, 'GSM', 'car')
    date_time=datetime.datetime(year,month,day,hour,min,sec)
    date_time_str=date_time.strftime('%Y-%m-%dT%H:%M:%S')
    coord.ticks = Ticktock(date_time_str, 'ISO')
    coord_new = coord.convert('GSE','car')
    GSE_XYZ=coord_new.data[0]
    
    # print (GSE_XYZ)
    # print (type(GSE_XYZ))
    
    return GSE_XYZ
    
def GSE2GSM(year,month,day,hour,min,sec,GSE_XYZ):
    # 功能：GSM坐标系->GSE坐标系
    coord = Coords(GSE_XYZ, 'GSE', 'car')
    date_time=datetime.datetime(year,month,day,hour,min,sec)
    date_time_str=date_time.strftime('%Y-%m-%dT%H:%M:%S')
    coord.ticks = Ticktock(date_time_str, 'ISO')
    coord_new = coord.convert('GSM','car')
    GSM_XYZ=coord_new.data[0]
    return GSM_XYZ
    
def read_data(fullpath):
    data={}
    if not os.path.exists(fullpath):
        return data

    fh=open(fullpath)
    # for line in fh.readlines()[0:20]:
        # print(line.strip())
    
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

        # Bx=float(lineList[7])     if float(lineList[7])!=MissingVal else np.nan
        # By=float(lineList[8])     if float(lineList[8])!=MissingVal else np.nan
        # Bz=float(lineList[9])     if float(lineList[9])!=MissingVal else np.nan
        # Bt=float(lineList[10])    if float(lineList[10])!=MissingVal else np.nan
        # lat=float(lineList[11])   if float(lineList[11])!=MissingVal else np.nan
        # lon=float(lineList[12])   if float(lineList[12])!=MissingVal else np.nan
                               
        Bx=float(lineList[7])  
        By=float(lineList[8])  
        Bz=float(lineList[9])  
        Bt=float(lineList[10]) 
        lat=float(lineList[11])
        lon=float(lineList[12])
        
        GSM_XYZ=[Bx,By,Bz]
        GSE_XYZ=GSM2GSE(YR,MO,DA,HH,MM,0,GSM_XYZ)
        Bx_GSE=GSE_XYZ[0]  
        By_GSE=GSE_XYZ[1]  
        Bz_GSE=GSE_XYZ[2]
        
        
        Bx_GSE = float(Bx_GSE)
        By_GSE = float(By_GSE)
        Bz_GSE = float(Bz_GSE)
        
        # print (GSE_XYZ[0])
        # print (GSE_XYZ[1])
        # print (GSE_XYZ[2])
        
        # print (Bx_GSE)
        # print (type(Bx_GSE))
        # input()
        
        
        # print(GSM_XYZ,'->',GSE_XYZ)

        timeStamp=datetime.datetime(YR,MO,DA,HH,MM)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M')
        format='%s'+3*'%6d'+6*'%10.2e'
        #print(format%(strTimeStamp,Day,Sec,S,Bx,By,Bz,Bt,lat,lon))
        
        # 绘图
        # data[timeStamp]={
            # 'S':  S,
            # 'Bx': Bx,
            # 'By': By,
            # 'Bz': Bz,
            # 'Bt': Bt,
            # 'Lat':lat,
            # 'Lon':lon,
            # 'Bx_GSE': Bx_GSE,
            # 'By_GSE': By_GSE,
            # 'Bz_GSE': Bz_GSE,
            # 'website':'SWPC',
            # 'category_abbr_en':'SWPC_ace_mag1m'}
            
        # # 入库
        data[strTimeStamp]={
            'S':  S,
            'Bx': Bx,
            'By': By,
            'Bz': Bz,
            'Bt': Bt,
            'Lat':lat,
            'Lon':lon,
            'Bx_GSE': Bx_GSE,
            'By_GSE': By_GSE,
            'Bz_GSE': Bz_GSE,
            'website':'SWPC',
            'category_abbr_en':'SWPC_ace_mag1m'}
    print (data)
    
    return data
    
def plot_data(data):
    if data=={}:
        return
        
    timeStampArr=[]
    BxArr,ByArr,BzArr,BtArr,latArr,lonArr=[],[],[],[],[],[]
    BxArr_GSE,ByArr_GSE,BzArr_GSE=[],[],[]
    for key in data.keys():
        timeStamp=key
        Bx=data[key]['Bx']
        By=data[key]['By']
        Bz=data[key]['Bz']
        Bx_GSE=data[key]['Bx_GSE']
        By_GSE=data[key]['By_GSE']
        Bz_GSE=data[key]['Bz_GSE']
        Bt=data[key]['Bt']
        lat=data[key]['Lat']
        lon=data[key]['Lon']
        
        
        timeStampArr.append(timeStamp)
        BxArr.append(Bx)
        ByArr.append(By)
        BzArr.append(Bz)
        BtArr.append(Bt)
        latArr.append(lat)
        lonArr.append(lon)
        BxArr_GSE.append(Bx_GSE)
        ByArr_GSE.append(By_GSE)
        BzArr_GSE.append(Bz_GSE)
        
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)	
    
    ax1 = plt.subplot(4,1,1)
    plt.plot(timeStampArr, BxArr)
    plt.plot(timeStampArr, BxArr_GSE)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-20,20])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Bx',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('1-minute averaged Real-time Interplanetary Magnetic Field Values',fontdict=font)
    plt.grid()
    
    ax1 = plt.subplot(4,1,2)
    plt.plot(timeStampArr, ByArr)
    plt.plot(timeStampArr, ByArr_GSE)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-20,20])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('By',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    ax1 = plt.subplot(4,1,3)
    plt.plot(timeStampArr, BzArr)
    plt.plot(timeStampArr, BzArr_GSE)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([-20,20])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Bz',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    ax1 = plt.subplot(4,1,4)
    plt.plot(timeStampArr, BtArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+datetime.timedelta(minutes=1)])
    plt.ylim([0,30])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Bt',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
    
    plt.savefig('ace_mag.png')
    plt.show()	

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='20190805_ace_mag_1m.txt'    
    fullpath=cwd+'/'+filename
    
    
    fullpath = '/home/YJY015/code/element_opt/20200723_ace_mag_1m_20200723_010000.txt'
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)
    
