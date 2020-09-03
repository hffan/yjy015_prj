#--coding:utf-8--
# date:     2019-08-14
# function: read Daily local noon solar radio flux values - Updated once an hour

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
    
    # 读取头信息
    fh=open(fullpath)
    linesOfHeader=12
    lines=fh.readlines()
    for line in lines[0:linesOfHeader]:
        print(line.strip())
    
    # 读取台站日期信息
    stations=lines[10].strip().split(' '*2)
    hours=lines[11].strip().split(' '*2)
    for idx in range(1,len(hours)):
        hours[idx]=int(hours[idx].split()[0][0:2])
    print(stations)
    print(hours)
    
    # 读取频点流量信息
    fh=open(fullpath)
    for line in fh.readlines()[linesOfHeader:]:
        # print(line.rstrip())
        lst=line.strip().split()
        
        if len(lst)==0:
            continue
        elif len(lst)==3:
            year=int(lst[0])
            month=list(calendar.month_abbr).index(lst[1])
            day=int(lst[2])
        else:
            for idx in range(1,len(lst)):
                fre=lst[0]
                hour=hours[idx]
                station=stations[idx]
                flux=lst[idx]
                timeStamp=datetime.datetime(year,month,day,hour)
                strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M:%S')
                
                if strTimeStamp not in data.keys():
                    data[strTimeStamp]={}

                if station not in data[strTimeStamp].keys():
                    data[strTimeStamp][station]={}
                    
                data[strTimeStamp][station][fre]={
                    'flux':flux,
                    'website':'SWPC',
                    'category_abbr_en':'SWPC_Solar_rad'}
    
    for key1 in data.keys(): 
        for key2 in data[key1].keys():
            print(key1,key2,data[key1][key2])
    
    return data
        
if __name__ == '__main__':
    # 1，获取数据文件全路径
    cwd = os.getcwd()
    filename='rad.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
