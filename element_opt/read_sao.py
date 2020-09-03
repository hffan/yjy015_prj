#--coding:utf-8--
# date:     2019-08-09
# function: read Geomagnetic Planetary Indices Kp

import os
import sys
import time
import calendar
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re

sys.path.append("..")#上层目录引入搜索路径
from cfg.conf import *

matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'

def read_data(fullpath):
    data={}
    if not os.path.exists(fullpath):
        return data
        
    lenOfRecord=[]
    recordOfLine=[]
    
    # fh=open('format.lst')
    formatpath = configs['formatpath']
    fh=open(formatpath)
    
    for line in fh.readlines():
        lineList=list(line.strip().split())
        lenOfRecord.append(int(lineList[1]))
        recordOfLine.append(int(lineList[0]))
    
    fh = open(fullpath)
    dataFileIndex=[]
    line1=list(re.findall(r'.{3}',fh.readline().rstrip()))
    line2=list(re.findall(r'.{3}',fh.readline().rstrip()))
    dataFileIndex=line1+line2[:20]
    dataFileIndex=np.array(list(map(int,dataFileIndex)))
    linesOfGroup=np.ceil(dataFileIndex/recordOfLine)

    numOfgroup=60
    groups=[[] for gid in range(numOfgroup)]
    
    for gid in range(numOfgroup):
        group=[]
        for id in range(int(linesOfGroup[gid])):
            line=fh.readline().rstrip()
            # print(line)
            format='.{'+str(lenOfRecord[gid])+'}'
            res=re.findall(format, line)
            if lenOfRecord[gid]>len(line):
                res=[line]
            group.extend(res)
            
        if gid==2 and group!=[]:
            date_time=datetime.datetime.strptime(''.join(group[2:20]),'%Y%j%m%d%H%M%S')
            str_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
            # print(date_time)
            
        if gid==3and group!=[]:
            foF2=float(group[0].strip())
            foF1=float(group[1].strip())
            M   =float(group[2].strip())
            MUF =float(group[3].strip())
            fmin=float(group[4].strip())
        # print(id,group)	
            
    data[str_date_time]={
         'site':'北京站',
         'TEC':-9999.0,
         'foF2':foF2,
         'foF1':foF1,
         'M':M,
         'MUF':MUF,
         'fmin':fmin,		
         'website':'NGDC',
        'category_abbr_en':'NGDC_BP440_SAO'}
    # print( data[str_date_time])
    #return res
    return data        
        
if __name__ == '__main__':
    cwd = os.getcwd()
    os.chdir(cwd)
    
    # BP440_2019001000001	
    year,doy,hour,min,sec=2019,1,0,0,1	
    filename = 'Bp440_'+str(year)+\
        str(doy).rjust(3,'0')+\
        str(hour).rjust(2,'0')+\
        str(min).rjust(2,'0')+\
        str(sec).rjust(2,'0')+'.SAO'
    read_data(filename)
