# -*- coding: utf-8 -*-


"""
@user guide:






@modify history:
2020-06-11 19:11:57 
                    1. 测试 SOHO日冕仪观测数据	太阳	GMU SOHO日冕仪观测数据	GMU_SOHO_COR2    http://spaceweather.gmu.edu/seeds/realtime/YYYY/MM/c2_png/	YYYYMMDD_hhmm_c2.gif	YYYYMMDD_hh*_c2.gif	/solar/GMU/SOHO/COR2/YYYYMM/YYYYMMDD	YYYYMMDD_hhmm_c2_YYYYMMDD_hhmmss.gif	gif	2	1次/12分钟	12
                    
                    
2020-06-15 10:10:07
                    1. cd /home/YJY015/code; python3 manually_task.py GMU_SOHO_COR2 2020-06-01 2020-06-01
                    2. 第1个参数：数据种类英文标识
                    3. 第2个参数：开始时间，是UTC时间，格式yyyy-mm-dd
                    4. 第3个参数：结束时间，是UTC时间，格式yyyy-mm-dd
                    
2020-06-16 17:39:08
                    1. 历史数据下载、可以重复
                    
2020-08-20 11:30:10
                    1. cd /home/YJY015/code; python3 /home/YJY015/code/manually_task.py GFZ_Kp_web 2020-06-01 2020-06-01 
                    2. 历史数据下载，正则匹配，可能会匹配多个文件，导致很多重复下载的文件，数量可能翻倍
                    
                    
                    
"""




import pytz
import os
import glob
import shutil
import sys
import logging
import re
import platform
import calendar
import datetime
import time
import traceback
import subprocess




from logger.logger import *
from db.postgres_archive import *
from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_current_BJT


from product_opt.product_gen import *
from event_alert_opt.alert_gen import *
from cfg.conf import *




def get_download_hour_minute_second(scheduling_interval_min):
    """
    1. 根据每日收集的数据量，来推算启动小时，再取1/12,比如1天下载1个文件，间隔24小时，1/12就是2小时，120分钟
    2. 可以redo，带日期格式的，需要带延迟下载，如果不带日期的文件，直接下载，不需要延迟
    3. 
        minute_clock = [m for m in range(0,60,15)]
        minute_clock
        [0, 15, 30, 45]
    """
    
    # 计算调度时间
    hours=[]
    mins=[]
    secs=[]
    for scheduling_real in range(0,1440,scheduling_interval_min):
        scheduling_delayed=scheduling_real
        ihour=(scheduling_delayed//60)%24
        imin=scheduling_delayed%60
        
        hours.append('%02d'%ihour)
        mins.append('%02d'%imin)

    hours=list(set(hours))
    mins=list(set(mins))
    hours.sort()
    mins.sort()
    secs.append('00')
    
    
    task_hour=','.join(hours)
    task_minute=','.join(mins)
    task_second = '00'
    
    
    #print('每日调度启动时刻：')
    #print('hour=',task_hour)
    #print('min =',task_min)
    
    #return task_hour,task_minute,task_second    
    return hours,mins,secs     
    
    
    
    
def get_download_time(starttime,task_hour,task_minute,task_second):
    download_starttime=[]
    for hour in task_hour:
        ####因为下载历史数据,1个小时内的文件,会模糊匹配多个文件,只取到小时即可
        # for minute in task_minute[0]:
        #for minute in task_minute:
        minute = task_minute[0]
        for second in task_second:
        
            yyyymmdd_HHMMSS = starttime + ' ' + hour + ':' + minute + ':' + second
            # print (task_minute,task_minute[0],hour,minute,second)
            # print (yyyymmdd_HHMMSS)
            yyyymmddHHMMSS  = (datetime.datetime.strptime(yyyymmdd_HHMMSS, "%Y-%m-%d %H:%M:%S")).strftime('%Y%m%d%H%M%S')
            download_starttime.append(yyyymmddHHMMSS)
    return download_starttime
    
    
    
# def get_download_time(starttime,task_hour,task_minute,task_second):
    # download_starttime=[]
    # for hour in task_hour:
        # ####因为下载历史数据,1个小时内的文件,会模糊匹配多个文件,只取到小时即可
        # # for minute in task_minute[0]:
        # for minute in task_minute:
            # ##minute = task_minute[0]
            # for second in task_second:
            
                # yyyymmdd_HHMMSS = starttime + ' ' + hour + ':' + minute + ':' + second
                # # print (task_minute,task_minute[0],hour,minute,second)
                # # print (yyyymmdd_HHMMSS)
                # yyyymmddHHMMSS  = (datetime.datetime.strptime(yyyymmdd_HHMMSS, "%Y-%m-%d %H:%M:%S")).strftime('%Y%m%d%H%M%S')
                # download_starttime.append(yyyymmddHHMMSS)
    # return download_starttime

    
    
def download_job(searchinfo,starttime,endtime,exe_path=os.path.dirname(os.path.abspath(__file__)),exe_name = 'download.py'):

    #db_name = 'yjy015'
    db_name = configs['db_name']    
    #table_name = 'data_monitor'
    
    ####传入的数据库记录，解析各个字段
    category_abbr_en = searchinfo['category_abbr_en']
    category_name_zh = searchinfo['category_name_zh']
    #task_triggers = searchinfo['task_triggers']
    data_class      = searchinfo['data_class']
    research_area   = searchinfo['research_area']
    website         = searchinfo['website']
    num_collect_perday      = int(searchinfo['num_collect_perday'])
    num_store_perday        = int(searchinfo['num_store_perday'])
    scheduling_interval_min = int(searchinfo['scheduling_interval_min'])
    scheduling_delayed_min  = int(searchinfo['scheduling_delayed_min'])
    task_name = '数据收集 ' + category_name_zh + ' ' + category_abbr_en
            
    ####任务启动时间，使用UTC时间启动，因为网站更新数据的时间是UTC时间
    task_starttime = get_current_UTC()
    log_starttime  = get_current_BJT()
    
    ####实例化日志类
    loggings=Loggings(log_starttime,category_abbr_en)
    
    ####配置命令行参数
    exe_fullpath = os.path.join(exe_path,exe_name)
    #starttime = (datetime.datetime.strptime(taskStarttime, "%Y-%m-%d %H:%M:%S")).strftime('%Y%m%d%H%M%S')
    ##加入延迟时间 ，延迟下载，根据延迟时间，下载当前时间 往前推算延迟时间的时刻，开始启动任务下载
    #starttime = (datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S")).strftime('%Y%m%d%H%M%S')
    ####调度推迟5分钟，实际下任务的时间，也得推算到5分钟之前的时间
    
    # starttime = (datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S")).strftime('%Y%m%d%H%M%S')
    # endtime = starttime


    ####启动任务
    cmd = 'python3' + ' ' + exe_fullpath + ' ' + category_abbr_en + ' ' + starttime + ' ' + endtime
    print (cmd)
    
    ####方案2，管道调用
    ####如果异常，可能没有返回值
    ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=None)    
    #ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=1)
    
    
    """
    1. ret.returncode == 0不能确定下载任务是否完成，需要根据下载任务返回状态信息，一起判别才作为此任务成功的标志
    
    """
    ####满足3个条件的基本没有，很少
    #if ret.returncode == 0 and ret.stderr == '' and ret.stdout == '':
    if ret.returncode == 0:    
        status = 'True'
        log = '成功'
        """ret返回的stdout，把屏幕输出的内容全部赋值给stdout"""
        #print("success:",ret)
        #print("success:",ret)        
    else:
        status = 'False'
        ##log只记录成功和失败，失败的详细原因记录到任务日志里
        #log = ret.stderr
        log = '失败'      
        loggings.debug_log('ret.returncode = %d'% ret.returncode)#输出hadoop异常操作到log日志里           
        loggings.debug_log(ret.stderr)#输出hadoop异常操作到log日志里
        #print (cmd)
        #print ("error:",ret.stderr)        
    
    
    return
    
    

    
    
    
if __name__ == '__main__':
    
    """
    1. 命令行cd /home/YJY015/code; python3 manually_task.py GMU_SOHO_COR2 2020-06-01 2020-06-01
    
    """
    
    
    if(len(sys.argv)==4):
        f_print('sys.argv[0] = %s'%sys.argv[0])  
        f_print('sys.argv[1] = %s'%sys.argv[1])  
        f_print('sys.argv[2] = %s'%sys.argv[2])  
        f_print('sys.argv[3] = %s'%sys.argv[3])   
        
        exe = sys.argv[0]                       #### manually_task.py
        category_abbr_ens=sys.argv[1]           #### 
        starttime=sys.argv[2]                   #### 时间是UTC时间,精确到天,而且是1天的开始时间,比如2020-06-01,实际时间应该按20200601000000~20200601235959计算
        endtime=sys.argv[3]                     #### 时间是UTC时间,精确到天,而且是1天的结束时间,比如2020-06-02,实际时间应该按20200602000000~20200602235959计算
            
            
    #### 读取任务数据库配置信息
    pga=PostgresArchive()
    
    db_name     =   configs['db_name'] 
    table_name  =   'data_category'
    searchinfos =   pga.search_db_table_usercmd(database_name=db_name,sqlcmd='select * from %s' % table_name)    
    
    
    ####方案2，从数据库查询，并添加任务
    for searchinfo in searchinfos:
        category_name_zh = searchinfo['category_name_zh']
        category_abbr_en = searchinfo['category_abbr_en']
        
        
        num_collect_perday      = int(searchinfo['num_collect_perday'])
        scheduling_interval_min = int(searchinfo['scheduling_interval_min'])
        scheduling_delayed_min  = int(searchinfo['scheduling_delayed_min'])
        website_status          = searchinfo['website_status']
        redo_flag               = searchinfo['redo_flag']
        
        save_path               = searchinfo['save_path']
        ####不是下载配置的数据,直接跳过
        if category_abbr_ens != category_abbr_en:
            continue
        ####如果网站停止更新，但是可以下载历史数据，所以网站状态，对于下载历史数据功能没有影响
        ####第1步，先判断网站有效性，如果网站状态停止更新,则此任务不需要启动
        # if('False' == website_status):
            # continue

        
        ####
        task_hour,task_minute,task_second = get_download_hour_minute_second(scheduling_interval_min)
        
        
        while starttime <= endtime:
            ####解析任务启动时刻
            print ('save_path = %s'%save_path)
            print ('task_hour = %s'%task_hour)
            print ('task_minute = %s'%task_minute)
            print ('task_second = %s'%task_second)  
            #input()
            
            ####拼接每个下载时刻的时间
            download_starttimes = get_download_time(starttime,task_hour,task_minute,task_second)
            print (download_starttimes)       
            #input()
            
            for download_starttime in download_starttimes:
                # for num in range(num_collect_perday):
                ####每个下载任务,开始时间和结束时间统一按开始时间
                try:
                    download_job(searchinfo,download_starttime,download_starttime,exe_path=os.path.dirname(os.path.abspath(__file__)),exe_name = 'download.py')
                except Exception as e:
                    raise Exception(traceback.format_exc()) 
            
            ##每天的下载时刻下载,需要更新日期到第2天
            starttime = (datetime.datetime.strptime(starttime, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        
        
        