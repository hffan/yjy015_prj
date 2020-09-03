#--coding:utf-8--
# date:	 2020-05-24
# 功能： 压缩文件


import os
import sys
import time
import calendar
import datetime
import numpy as np
import shutil 
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess


from zipfile import ZipFile
from os import listdir
from os.path import isfile,isdir,join


def addFileIntoZipfile(srcLst,fp):
    for subpath in srcLst:
        if isfile(subpath):
            fp.write(subpath)   #写入文件
    return
    
    
def zipCompress(abs_srcLst,jason_fullpath,desZipfile):
    # ####删除已经存在的压缩文件，否则会一直追加
    # if os.path.exists(desZipfile):
        # os.remove(desZipfile)
    
    #获取zip文件路径
    path,name = os.path.split(desZipfile)
    
    #以追加模式打开或创建zip文件
    fp=ZipFile(desZipfile,mode='a')
    
    ##写入数据
    addFileIntoZipfile(abs_srcLst,fp)
    
    ##写入jason数据库记录文件,写入到zip文件里
    fp.write(jason_fullpath)
    
    fp.close()
    return
    
def zipCompress_data(abs_srcLst,desZipfile):
    # ####删除已经存在的压缩文件，否则会一直追加
    # if os.path.exists(desZipfile):
        # os.remove(desZipfile)
    
    #获取zip文件路径
    path,name = os.path.split(desZipfile)
    
    #以追加模式打开或创建zip文件
    fp=ZipFile(desZipfile,mode='a')
    
    ##写入数据
    addFileIntoZipfile(abs_srcLst,fp)
    
    
    fp.close()
    return

    
if __name__ == '__main__':	
    pass 
    # desZipfile='zipFile.zip'
    # if os.path.exists(desZipfile):
        # os.remove(desZipfile)
        
    # paths=['./schedule.py','./DOY.py','wget/wget.py']
    # zipCompress(paths,desZipfile)
    
    
    
    
    
    