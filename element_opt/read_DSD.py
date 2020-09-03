#--coding:utf-8--
# date:     2019-08-12
# function: read Daily Solar Data

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
    lineofheader=13
    for line in fh.readlines()[0:lineofheader]:
        print(line)
        
    fh=open(fullpath)
    for line in fh.readlines()[lineofheader:]:
        lineList=line.strip().split()
        year=int(lineList[0])
        month=int(lineList[1])
        day=int(lineList[2])
        F107=int(lineList[3])
        SunspotNum=int(lineList[4])
        SunspotArea=int(lineList[5])
        NewRegions=int(lineList[6])
        XRayBkgdFlux=float(lineList[8][1:]) if str.isdigit(lineList[8][1:]) else -999
        FlaresXRayC=int(lineList[9])
        FlaresXRayM=int(lineList[10])
        FlaresXRayX=int(lineList[11])
        FlaresOptS=int(lineList[12])
        FlaresOpt1=int(lineList[13])
        FlaresOpt2=int(lineList[14])
        FlaresOpt3=int(lineList[15])
        
        timeStamp=datetime.datetime(year,month,day)
        strTimeStamp=timeStamp.strftime('%Y-%m-%d')
        format='%s'+4*'%6d'+'%8.2f'+7*'%6d'
        # print(format%(strTimeStamp,F107,SunspotNum,SunspotArea,NewRegions,XRayBkgdFlux,\
            # FlaresXRayC,FlaresXRayM,FlaresXRayX,FlaresOptS,FlaresOpt1,FlaresOpt2,FlaresOpt3))
        
        # # 绘图
        # data[timeStamp]={
            # 'F107':F107,
            # 'SunspotNum':SunspotNum,
            # 'SunspotArea':SunspotArea,
            # 'NewRegions':NewRegions,
            # 'XRayBkgdFlux':XRayBkgdFlux,
            # 'FlaresXRayC':FlaresXRayC,
            # 'FlaresXRayM':FlaresXRayM,
            # 'FlaresXRayX':FlaresXRayX,
            # 'FlaresOpticalS':FlaresOptS,
            # 'FlaresOptical1':FlaresOpt1,
            # 'FlaresOptical2':FlaresOpt2,
            # 'FlaresOptical3':FlaresOpt3,
            # 'website':'SWPC',
            # 'category_abbr_en':'SWPC_latest_DSD'}
        
        # 入库
        data[strTimeStamp]={
            'F107':F107,
            'SunspotNum':SunspotNum,
            'SunspotArea':SunspotArea,
            'NewRegions':NewRegions,
            'XRayBkgdFlux':XRayBkgdFlux,
            'FlaresXRayC':FlaresXRayC,
            'FlaresXRayM':FlaresXRayM,
            'FlaresXRayX':FlaresXRayX,
            'FlaresOpticalS':FlaresOptS,
            'FlaresOptical1':FlaresOpt1,
            'FlaresOptical2':FlaresOpt2,
            'FlaresOptical3':FlaresOpt3,
            'website':'SWPC',
            'category_abbr_en':'SWPC_latest_DSD'}
            
        # for key in data.keys():
            # print(key,data[key])
            
    return data	

if __name__=='__main__':
    # 1，获取数据文件全路径
    cwd = os.getcwd()
    filename='DSD.txt'
    fullpath=cwd+'/'+filename
    
    # 2，读取数据
    data=read_data(fullpath)