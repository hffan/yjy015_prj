#--coding:utf-8--
# date:     2020-05-12
# function: read 1-minute GOES-16 data,json file

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
import math

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'

def cal_HAF(XRay_Flux):    
    # 功能：计算the Highest Affected Frequency
    # 输入：solar X-ray flux at 0.1-0.8 nm,(W·m-2)
    # 输出：the frequency which suffers a loss of 1 dB during vertical propagation from the ground, 
    #        through the ionosphere, and back to ground. HAF(MHz)
    
    # M1.0 -> 15 MHz
    # M5.0 -> 20 MHz
    # X1.0 -> 25 MHz
    # X5.0 -> 30 MHz
    if XRay_Flux>0:
        HAF= np.max([10*math.log10(XRay_Flux)+ 65,0])
    else:
        HAF=0
        
    return HAF
    
def solar_flare(P):    
    # 功能：太阳耀斑事件等级
    # 输入：X射线流量
    # 输出：太阳耀斑事件等级，共7级别
        
    measures={
        'L1':1E-8,
        'L2':1E-7,
        'L3':1E-6,
        'L4':1E-5,
        'L5':5E-5,
        'L6':1E-4,
        'L7':5E-4}
        
    # levels={
        # 'L1':'A',
        # 'L2':'B',
        # 'L3':'C',
        # 'L4':'M1',
        # 'L5':'M5',
        # 'L6':'X1',
        # 'L7':'X5',}
    levels={
        'L1':'A',
        'L2':'B',
        'L3':'C',
        'L4':'M1.0',
        'L5':'M5.0',
        'L6':'X1.0',
        'L7':'X5.0',}
        
    descrips={
        'L1':'',
        'L2':'',
        'L3':'',
        'L4':'',
        'L5':'',
        'L6':'',
        'L7':'强'}
    
    descrip=''
    level=''
    for key in descrips:
        if P>=measures[key]:
            descrip=descrips[key]
            level=levels[key]
    return level,descrip
    
def read_data(fullpath):
    data={}
    if not os.path.exists(fullpath):
        return data
        
    fh = open(fullpath,encoding='utf-8')
    content = fh.read()         #使用loads()方法需要先读文件
    lst = json.loads(content)    #loads()返回结果为list
    
    num=len(lst)                #记录个数
    # {"time_tag": "2020-05-10T02:40:00Z", 
    #  "satellite": 16, 
    #  "flux": 7.3816797e-09, 
    #  "energy": "0.05-0.4nm"}, 
    
    for rec in lst:
        time_tag=rec["time_tag"]
        timeStamp=datetime.datetime.strptime(time_tag,'%Y-%m-%dT%H:%M:%SZ')
        str_timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        
        satellite='GOES'+str(rec["satellite"])
        flux=rec["flux"]
        energy=rec["energy"]
        
        # # 绘图
        # if timeStamp not in data.keys():
            # data[timeStamp]={
                # 'XR_short':np.nan,
                # 'XR_long':np.nan,
                # 'HAF':np.nan,
                # 'level':'',
                # 'descrip':'',
                # 'satellite':satellite,
                # 'time_resolution':1,
                # 'website':'SWPC',
                # 'category_abbr_en':'SWPC_GOES_XR1m'}
                
        # if energy=="0.05-0.4nm":
            # data[timeStamp]['XR_short']=flux
        # elif energy=="0.1-0.8nm":
            # data[timeStamp]['XR_long']=flux
            # data[timeStamp]['HAF']=cal_HAF(flux)
            # level,descrip=solar_flare(flux)
            # data[timeStamp]['level']=level
            # data[timeStamp]['descrip']=descrip
        # else:
            # continue
        
        # 入库
        if str_timeStamp not in data.keys():
            data[str_timeStamp]={
                'XR_short':-9999.0,
                'XR_long':-9999.0,
                'HAF':0,
                'level':'',
                'descrip':'',
                'satellite':satellite,
                'time_resolution':1,
                'website':'SWPC',
                'category_abbr_en':'SWPC_GOES_XR1m'}
                
        if energy=="0.05-0.4nm":
            data[str_timeStamp]['XR_short']=flux
        elif energy=="0.1-0.8nm":
            data[str_timeStamp]['XR_long']=flux
            data[str_timeStamp]['HAF']=cal_HAF(flux)
            level,descrip=solar_flare(flux)
            data[str_timeStamp]['level']=level
            data[str_timeStamp]['descrip']=descrip
        else:
            continue
        
    # for key in data.keys():
        # print(key,data[key])
        
    return data
    
def plot_data(data,fullpath):
    if data=={}:
        return
        
    timeStampArr=[]
    shortArr,longArr=[],[]
    for key in data.keys():
        timeStamp=key
        short=data[key]['XR_short']
        long=data[key]['XR_long']
        timeStampArr.append(timeStamp)
        shortArr.append(short)
        longArr.append(long)
        
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)    
    
    ax1 = plt.subplot(1,1,1)
    h1,=plt.plot(timeStampArr, shortArr)
    h2,=plt.plot(timeStampArr, longArr)
    plt.xlim([timeStampArr[0],timeStampArr[-1]+(timeStampArr[1]-timeStampArr[0])])
    plt.ylim([0,1E-7])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Xray Flux',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels]
    plt.legend(handles = [h1,h2],\
        labels = ['short','long'],\
        loc = 'best',\
        prop={'family':'Times New Roman','size':10})
    plt.title('GOES Solar X-ray Flux',fontdict=font)
    plt.grid()
    
    savepath=fullpath.replace('.json','.png')
    plt.savefig(savepath)
    plt.show()    

if __name__ == '__main__':
    fullpath='xrays-1-day.json'
    data=read_data(fullpath)
    plot_data(data,fullpath)