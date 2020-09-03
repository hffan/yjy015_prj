#--coding:utf-8--
# date:     2019-08-14
# function: read 5-minute averaged Real-time Differential Electron and Proton Flux

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
    for line in fh.readlines()[0:18]:
        print(line.strip())
    
    fh=open(fullpath)
    for line in fh.readlines()[18:]:
        lineList=list(line.strip().split())
        YR=int(lineList[0])
        MO=int(lineList[1])
        DA=int(lineList[2])
        HH=int(lineList[3][0:2])
        MM=int(lineList[3][2:])        
        Day=int(lineList[4])   
        Sec=int(lineList[5])
        
        # EleS=int(lineList[6])
        # EleDiffFlux_38to53=float(lineList[7])       if float(lineList[7])!=-1.00e+05 else np.nan
        # EleDiffFlux_175to315=float(lineList[8])     if float(lineList[8])!=-1.00e+05 else np.nan 
        # ProS=int(lineList[9])
        # ProDiffFlux_47to68=float(lineList[10])      if float(lineList[10])!=-1.00e+05 else np.nan  
        # ProDiffFlux_115to195=float(lineList[11])    if float(lineList[11])!=-1.00e+05 else np.nan
        # ProDiffFlux_310to580=float(lineList[12])    if float(lineList[12])!=-1.00e+05 else np.nan 
        # ProDiffFlux_795to1193=float(lineList[13])   if float(lineList[13])!=-1.00e+05 else np.nan
        # ProDiffFlux_1060to1900=float(lineList[14])  if float(lineList[14])!=-1.00e+05 else np.nan 
        # AnisIndex=float(lineList[15])
            
        EleS=int(lineList[6])
        EleDiffFlux_38to53=float(lineList[7])     
        EleDiffFlux_175to315=float(lineList[8])    
        ProS=int(lineList[9])
        ProDiffFlux_47to68=float(lineList[10])     
        ProDiffFlux_115to195=float(lineList[11])  
        ProDiffFlux_310to580=float(lineList[12])  
        ProDiffFlux_795to1193=float(lineList[13]) 
        ProDiffFlux_1060to1900=float(lineList[14])
        AnisIndex=float(lineList[15])
                
        timeStamp=datetime.datetime(YR,MO,DA,HH,MM)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d %H:%M')
        # format='%s'+3*'%6d'+2*'%10.2e'+1*'%6d'+5*'%10.2e'+'%6d'
        # print(format%(strTimeStamp,Day,Sec,\
            # EleS,EleDiffFlux_38to53,EleDiffFlux_175to315,\
            # ProS,ProDiffFlux_47to68,ProDiffFlux_115to195,\
            # ProDiffFlux_310to580,ProDiffFlux_795to1193,ProDiffFlux_1060to1900,AnisIndex))
        
        # 绘图
        # data[timeStamp]={
            # 'EleS':                  EleS,
            # 'EleDiffFlux_38to53':    EleDiffFlux_38to53,
            # 'EleDiffFlux_175to315':  EleDiffFlux_175to315,
            # 'ProS':                  ProS,
            # 'ProDiffFlux_47to68':    ProDiffFlux_47to68,
            # 'ProDiffFlux_115to195':  ProDiffFlux_115to195,
            # 'ProDiffFlux_310to580':  ProDiffFlux_310to580,
            # 'ProDiffFlux_795to1193': ProDiffFlux_795to1193,
            # 'ProDiffFlux_1060to1900':ProDiffFlux_1060to1900,
            # 'AnisIndex':             AnisIndex,
            # 'website': 'SWPC',
            # 'category_abbr_en':'SWPC_ace_ep5m'}
         
        # 入库
        data[strTimeStamp]={
            'EleS':                  EleS,
            'EleDiffFlux_38to53':    EleDiffFlux_38to53,
            'EleDiffFlux_175to315':  EleDiffFlux_175to315,
            'ProS':                  ProS,
            'ProDiffFlux_47to68':    ProDiffFlux_47to68,
            'ProDiffFlux_115to195':  ProDiffFlux_115to195,
            'ProDiffFlux_310to580':  ProDiffFlux_310to580,
            'ProDiffFlux_795to1193': ProDiffFlux_795to1193,
            'ProDiffFlux_1060to1900':ProDiffFlux_1060to1900,
            'AnisIndex':             AnisIndex,
            'website': 'SWPC',
            'category_abbr_en':'SWPC_ace_ep5m'}

    return data
    
def plot_data(data):
    if data=={}:
        return
        
    timeStampArr=[]
    EleDiffFlux_38to53Arr,EleDiffFlux_175to315Arr=[],[]
    for key in data.keys():
        timeStamp=key
        EleDiffFlux_38to53=data[key]['EleDiffFlux_38to53']
        EleDiffFlux_175to315=data[key]['EleDiffFlux_175to315']
        
        timeStampArr.append(timeStamp)
        EleDiffFlux_38to53Arr.append(EleDiffFlux_38to53)
        EleDiffFlux_175to315Arr.append(EleDiffFlux_175to315)
    
    font={
        'family':'Times New Roman',\
        'style':'normal',\
        'weight':'normal',\
        'color':'black',\
        'size':12
        }
        
    plt.figure(figsize=(8, 6), dpi=150)    
    
    ax1 = plt.subplot(2,1,1)
    plt.plot(timeStampArr, EleDiffFlux_38to53Arr,'-.')
    plt.xlim([timeStampArr[0],timeStampArr[-1]])
    # plt.ylim([0,100])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('38-53 Kev',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax1.get_xticklabels() + ax1.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.title('5-minute averaged Real-time Differential ElectronFlux',fontdict=font)
    plt.grid()
    
    ax2 = plt.subplot(2,1,2)
    plt.plot(timeStampArr, EleDiffFlux_175to315Arr,'-')
    plt.xlim([timeStampArr[0],timeStampArr[-1]])
    # plt.ylim([0,100])
    plt.xlabel('UT',fontdict=font)
    plt.ylabel('175-315 Kev',fontdict=font)
    plt.tick_params(labelsize=10)
    labels = ax2.get_xticklabels() + ax2.get_yticklabels()
    [label.set_fontname('Times New Roman') for label in labels] 
    plt.grid()
        
    plt.savefig('ace_epam.png')
    plt.show()    

if __name__ == '__main__':
    # 1，获取文件全路径
    cwd = os.getcwd()
    filename='20190805_ace_epam_5m.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)
    
    # 3，绘制图像
    plot_data(data)
    
