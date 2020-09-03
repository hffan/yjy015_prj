#--coding:utf-8--
# date:     2020-05-12
# function: read 1-minute GOES-16 integral electrons data ,json file

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

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'

def electron_burst(P):    
    # 功能：高能电子暴事件等级
    # 输入：过去24小时高能电子积分通量
    # 输出：高能电子暴事件等级，共3级别
        
    measures={
        'L1':1E8,
        'L2':1E9,
        'L3':3E9}
   
    levels ={
        'L1':'弱',
        'L2':'强',
        'L3':'超强'}
     
    descrips={
        'L1':'',
        'L2':'强',
        'L3':'超强'}
    
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
    content = fh.read() 		#使用loads()方法需要先读文件
    lst = json.loads(content)	#loads()返回结果为list
    
    num=len(lst)				#记录个数
    
    # 单条记录格式
    # {"time_tag": "2020-05-10T02:45:00Z", 
    #  "satellite": 16, 
    #  "flux": 0.522027313709259, 
    #  "energy": ">=1 MeV"}, 
    
    energy_dic={">=2 MeV":'EFgt2d0M'}	
    
    IEFday=0        # 日积分通量
    for rec in lst:
        time_tag=rec["time_tag"]
        timeStamp=datetime.datetime.strptime(time_tag,'%Y-%m-%dT%H:%M:%SZ')
        str_timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S')
        satellite=rec["satellite"]
        satellite='GOES'+str(satellite)
        flux=rec["flux"]
        energy=rec["energy"]
        
        if energy==">=2 MeV":
            IEFday=IEFday+flux*(5*60)   # 每五分钟一个值
        
        # # 绘图
        # if timeStamp not in data.keys():
            # data[timeStamp]={
                # 'EFgt0d8M':np.nan, 
                # 'EFgt2d0M':np.nan,             
                # 'EFgt4d0M':np.nan, 
                # 'IEFday':np.nan,          # 日积分通量      
                # 'level':'',               # 高能电子暴事件等级      
                # 'descrip':'',             # 高能电子暴事件等级      
                # 'satellite':satellite,
                # 'time_resolution':1,
                # 'website':'SWPC',
                # 'category_abbr_en':'SWPC_GOES_IE5m'}
        # data[timeStamp][energy_dic[energy]]=flux
        
        # 入库
        if str_timeStamp not in data.keys():
            data[str_timeStamp]={
                'EFgt0d8M':-9999.0, 
                'EFgt2d0M':-9999.0,                
                'EFgt4d0M':-9999.0,
                'IEFday':-9999.0,           # 日积分通量      
                'level':'',                 # 高能电子暴事件等级          
                'descrip':'',               # 高能电子暴事件等级          
                'satellite':satellite,
                'time_resolution':1,
                'website':'SWPC',
                'category_abbr_en':'SWPC_GOES_IE5m'}
        data[str_timeStamp][energy_dic[energy]]=flux
    # 入库
    level,descrip=electron_burst(IEFday)    
    data[str_timeStamp]['IEFday']=IEFday
    data[str_timeStamp]['level']=level
    data[str_timeStamp]['descrip']=descrip
    
    # for key in data.keys():
        # print(key,data[key])
    
    return data
    
def plot_data(data,fullpath):
    if data=={}:
        return
        
    energy_dic={">=2 MeV":'EFgt2d0M'}	
        
    plt.figure(figsize=(8, 6), dpi=150)	
    ax1 = plt.subplot(1,1,1)
    

    for energy in energy_dic.keys():
        timeStamps=[]
        fluxs=[]
        for key in data.keys():
            timeStamp=key
            timeStamps.append(key)
            flux=data[key][energy_dic[energy]]
            fluxs.append(flux)
        
        font={
            'family':'Times New Roman',\
            'style':'normal',\
            'weight':'normal',\
            'color':'black',\
            'size':12}
            
        plt.plot(timeStamps, fluxs)
        
    plt.xlim([timeStamps[0],timeStamps[-1]+(timeStamps[1]-timeStamps[0])])
    # plt.ylim([0,1E-7])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('Integral electrons Flux',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels]
    plt.legend(
        labels = [key for key in energy_dic.keys()],\
        loc = 'best',\
        prop={'family':'Times New Roman','size':10})
    plt.title('GOES-16 Integral electrons Flux',fontdict=font)
    plt.grid()
    
    savepath=fullpath.replace('.json','.png')
    plt.savefig(savepath)
    plt.show()	

if __name__ == '__main__':
    fullpath='integral-electrons-1-day.json'
    data=read_data(fullpath)
    plot_data(data,fullpath)