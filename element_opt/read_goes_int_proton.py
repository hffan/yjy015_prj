#--coding:utf-8--
# date:     2020-05-12
# function: read 1-minute GOES-16 integral protons data ,json file

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

def cal_SEP_Abs(J5d2MeV,J2d2MeV=0):
    # 功能：计算Ad and An, at the standard frequency 30 MHz 
    # 输入：the integral proton fluxes J above certain energy E thresholds
    # 输出：Ad and An
    
    # Ad = 0.115 [J(E>5.2 MeV)]1/2 dB
    # An = 0.020 [J(E>2.2 MeV)]1/2 dB
    
    if J5d2MeV>0:
        Ad=0.115*J5d2MeV**0.5
        An=0.020*J2d2MeV**0.5
    else:
        Ad=0
        An=0
    
    return Ad,An
    
def solar_proton(P):    
    # 功能：太阳质子事件等级
    # 输入：太阳质子通量
    # 输出：太阳质子事件等级，共4级别
        
    measures={
        'L1':1E1,
        'L2':1E2,
        'L3':1E3,
        'L4':1E4}
        
    levels={
        'L1':'1级',
        'L2':'2级',
        'L3':'3级',
        'L4':'4级'}
  
    descrips={
        'L1':'弱', 
        'L2':'中等',  
        'L3':'强',    
        'L4':'超强'}
    
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
    # {"time_tag": "2020-05-10T02:45:00Z", 
    #  "satellite": 16, 
    #  "flux": 0.522027313709259, 
    #  "energy": ">=1 MeV"}, 
    
    energy_dic={
        ">=1 MeV":'PFgt01M',
        ">=5 MeV":'PFgt05M',
        ">=10 MeV":'PFgt10M',
        ">=30 MeV":'PFgt30M',
        ">=50 MeV":'PFgt50M',
        ">=60 MeV":'PFgt60M',
        ">=100 MeV":'PFgt100M',
        ">=500 MeV":'PFgt500M'}	
        
    for rec in lst:
        time_tag=rec["time_tag"]
        timeStamp=datetime.datetime.strptime(time_tag,'%Y-%m-%dT%H:%M:%SZ')
        str_timeStamp = timeStamp.strftime('%Y-%m-%d %H:%M:%S')        
        satellite=rec["satellite"]
        satellite='GOES'+str(satellite)
        flux=rec["flux"]
        energy=rec["energy"]
        
        # # 绘图
        # if timeStamp not in data.keys():
            # data[timeStamp]={
                # 'PFgt01M':np.nan,
                # 'PFgt05M':np.nan,
                # 'PFgt10M':np.nan,
                # 'PFgt30M':np.nan,
                # 'PFgt50M':np.nan,
                # 'PFgt60M':np.nan,
                # 'PFgt100M':np.nan,
                # 'PFgt500M':np.nan,
                # 'Ad':np.nan,
                # 'An':np.nan,
                # 'level':'',
                # 'descrip':'',
                # 'satellite':satellite,
                # 'time_resolution':5,
                # 'website':'SWPC',
                # 'category_abbr_en':'SWPC_GOES_IP5m'}
        # data[timeStamp][energy_dic[energy]]=flux
        # if energy==">=5 MeV":
            # Ad,An=cal_SEP_Abs(flux)
            # data[timeStamp]['Ad']=Ad
            # data[timeStamp]['An']=An
        # if energy==">=10 MeV":
            # level,descrip=solar_proton(flux)
            # data[timeStamp]['level']=level
            # data[timeStamp]['descrip']=descrip
        
        # 入库
        if str_timeStamp not in data.keys():
            data[str_timeStamp]={
                'PFgt01M':-9999.0,
                'PFgt05M':-9999.0,
                'PFgt10M':-9999.0,
                'PFgt30M':-9999.0,
                'PFgt50M':-9999.0,
                'PFgt60M':-9999.0,
                'PFgt100M':-9999.0,
                'PFgt500M':-9999.0, 
                'Ad':0,
                'An':0,
                'level':'',
                'descrip':'',
                'satellite':satellite,
                'time_resolution':5,
                'website':'SWPC',
                'category_abbr_en':'SWPC_GOES_IP5m'}
        data[str_timeStamp][energy_dic[energy]]=flux
        if energy==">=5 MeV":
            Ad,An=cal_SEP_Abs(flux)
            data[str_timeStamp]['Ad']=Ad
            data[str_timeStamp]['An']=An
        if energy==">=10 MeV":
            level,descrip=solar_proton(flux)
            data[str_timeStamp]['level']=level
            data[str_timeStamp]['descrip']=descrip
     
    # for key in data.keys():
        # print(key,data[key])
        
    return data
    
def plot_data(data,fullpath):
    if data=={}:
        return
        
    energy_dic={
        ">=1 MeV":'PFgt01M',
        ">=5 MeV":'PFgt05M',
        ">=10 MeV":'PFgt10M',
        ">=30 MeV":'PFgt30M',
        ">=50 MeV":'PFgt50M',
        ">=60 MeV":'PFgt60M',
        ">=100 MeV":'PFgt100M',
        ">=500 MeV":'PFgt500M'}		
        
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
    plt.ylabel('Integral Protons Flux',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels]
    plt.legend(
        labels = [key for key in energy_dic.keys()],\
        loc = 'best',\
        prop={'family':'Times New Roman','size':10})
    plt.title('GOES-16 Integral Protons Flux',fontdict=font)
    plt.grid()
    
    savepath=fullpath.replace('.json','.png')
    plt.savefig(savepath)
    plt.show()	

if __name__ == '__main__':
    fullpath='integral-protons-1-day.json'
    data=read_data(fullpath)
    plot_data(data,fullpath)