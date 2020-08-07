#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
@user guide:
1. nohup linux后台启动此脚本
2. crontab里添加守护进程脚本，linux_daemon.sh，判断此脚本是否被杀，被杀直接启动
3. crontab里添加守护进程脚本，linux_daemon.sh，保证系统中只有1个生产脚本在启动
4. cd /home/YJY015/code; nohup python -u automatically_task.py >automatically_task.log 2>&1 &
5. 输出重定向，可以查看py文件是否执行的日志，也可以查看py文件否具有可执行权限
6. 查找进程， ps -ef|grep automatically_task.py.py
7. 杀进程，kill -9 PID




@modify history:

2020-05-07 10:01:13
                    1. 每次修改完t_task配置信息，需要先杀掉进程，再启动，否则读取到的数据库表信息是之前的配置信息
2020-05-08 16:34:39
                    1. 调度任务，使用subprocess后台启动，捕获日志，写入log日志文件，并写入监控数据库表
                    2. 如果系统时间时区是北京时，则显示的是北京时间，比如北京时间8：00，utc时间是00：00，每天早上8：00之后，可以看到当天的任务
2020-05-09 14:38:03
                    1. 调度使用UTC时间，获取系统时间使用UTC时间作为下载的starttime           
2020-05-12 19:29:16
                    1. 如果根据data_category里的website_status为False,需要杀掉调度任务,再重新启动任务调度
2020-05-15 09:04:59
                    1. 自动重做，需要改写task_monitor的状态，否则每天都去查找前3天的失败任务,状态没有改写导致重复的重做
                    2. 如何自动重做流程里没有重做成功，用户想通过手动重做，需要手动重做的接口,而且接口里需要改写task_monitor的状态信息
                    3. 带日期的，可以重做得，需要带延迟下载，不带日期的，需要实时下载
                    4. 调度该怎么下载就按UTC时间下载，延迟加到具体的某个任务里面，starttime,endtime还按UTC没有延迟的时间来
2020-05-20 11:15:42
                    1. 添加下载延迟，正则匹配使用list匹配规则
                    2. 需要添加调度读取数据库参数配置，如果数据库配置信息更改，调度自动读取数据库配置信息，而不是只在第1次启动的时候读取
2020-05-21 16:01:01
                    1. 每天早上06：00：00，开始重做前3天的失败任务，并更新task_monitor数据库
2020-05-21 16:55:42
                    1. 延迟下载，根据延迟时间，当前时间往前推算延迟时间，单位是分钟，那一时刻开始启动任务下载
                    2. ret.returncode有bug，返回值成功与否，不能做为判断依据
2020-05-22 14:30:06
                    1. 根据延迟时间，推算启动时间，最后下载的UTC时间，还是延迟之前的时刻
2020-05-25 13:25:04 
                    1. 业务的主程序main，更新为download，导致task_monitor记录里的cmd命令找不到主程序，正式上线，不能随意更改文件名
                    2. 如果手动清除了apscheduler.log和automatically_task.log日志文件，导致进程挂起为Sleeping状态
2020-05-26 10:58:37
                    1. log写入规则，成功没有错误，直接写入成功，如果失败，直接写失败的详细原因，不写简单的失败，否则不利于定位问题                    
2020-05-27 16:07:38
                    1. 产品生产，需要查询数据，因为调度容错，带来1-2秒数据，导致查询的start_time会有1-2秒误差，最大发现有7秒误差，导致查询失败，设置查询秒00~59范围的数据
                    2. 实际测试发现数据收集任务会丢，但是对应的产品生产任务没有丢，导致产品生产从数据库里查询数据失败
2020-05-29 10:56:26
                    1. alert_monitor监控表里，录入alert_type，不是录入数据来源英文标识                    
2020-06-04 18:44:44
                    1. 如果警报kp，3小时1个值，15分钟启动1次，如果到了18点刚好更新了1个值，18：15，18：30......，会一直发警报，应该是3小时发一次警报
2020-06-10 16:17:19
                    1. download功能中，data_monitor记录的个数比data_file_info少，原因是data_file_info，在正则匹配的时候，出现for循环一次下载多个文件，而data_monitor只记录1次
2020-07-10 18:06:32 
                    1. kill_process每天晚上20:00开始查杀
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


from apscheduler.schedulers.background import BackgroundScheduler               #非阻塞方式
from apscheduler.schedulers.blocking import BlockingScheduler                   #阻塞方式

from apscheduler.events import (EVENT_JOB_EXECUTED,EVENT_JOB_ERROR)
from apscheduler.triggers.cron import CronTrigger                               #制定触发器

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from socket_interface.sockets import *

##实例化类名，类初始化的变量，动画滑动窗口，只能实例化一次
import event_alert_opt.electron_burst
import event_alert_opt.geomag_storm
import event_alert_opt.solar_flare
import event_alert_opt.solar_proton



from logger.logger import *
from db.postgres_archive import *
from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_yesterday_UTC
from time_interface.time_format import get_current_BJT

from product_opt.product_gen import *
from event_alert_opt.alert_gen import *
from cfg.conf import *

        

# def get_task_hour_minute_second(redo_flag,num_collect_perday):
    # """
    # 1. 根据每日收集的数据量，来推算启动小时，再取1/12,比如1天下载1个文件，间隔24小时，1/12就是2小时，120分钟
    # 2. 可以redo，带日期格式的，需要带延迟下载，如果不带日期的文件，直接下载，不需要延迟
    
    # """
    
    # if redo_flag == 'False'：
        # delay_minute = 0
    # else:
        # delay_minute = 24*60/num_collect_perday/12
        # delay_minute = max(delay_minute,1)          ##最小不能小于1分钟，因为最小下载间隔是1分钟，推迟1分钟导致后1分钟的数据丢失
    
    # print (delay_minute)
    
    # ####推迟下载，一定不能跨天，否则下载的不是当天的数据
    # year    =   datetime.datetime.now().year
    # month   =   datetime.datetime.now().month
    # day     =   datetime.datetime.now().day
    
    # delay_task_hours=[]
    # delay_task_minutes=[]
    # #step_minute = 24*60/num_collect_perday
    
    # ####平分1天的24小时,时分秒都按整点处理
    # # for index_hour in range(num_collect_perday//60):
        # # #mod_hour = index_hour
        # # delay_task_hour.append(str(index_hour))
    
    # for index in range(num_collect_perday):
    # #for index_minute in range(num_collect_perday//24):
        # #mod_minute = index_minute
        # #print (index_hour,index_minute,mod_hour,mod_minute)
        
        # hour_clock = index//60       
        # minute_clock = index%24
        # print (hour_clock,minute_clock)
        # ####推迟分钟数，需要加推迟的分钟数，推迟时刻靠后，需要加整数
        # delay_date = datetime.datetime(year, month, day, hour_clock, minute_clock, 0) + datetime.timedelta( minutes=delay_minute)
        # delay_task_minute = delay_date.minute
        # delay_task_hour = delay_date.hour      
          
           
        # if index % 60:
            # delay_task_hours.append(str(delay_task_hour))    
        # if index % 24:
            # delay_task_minutes.append(str(delay_task_minute))

    
    # task_hour   = ','.join(delay_task_hours)
    # task_minute = ','.join(delay_task_minutes)    
    # task_second = '00'
    # #print (task_hour,task_minute,task_second)
    # #print (task_hour)
    # print (task_minute)
    # #print (task_second)        
    
    # return task_hour,task_minute,task_second
    


# def get_task_hour_minute_second(num_collect_perday):
    # """
    # 1. 根据每日收集的数据量，来推算启动小时，再取1/12,比如1天下载1个文件，间隔24小时，1/12就是2小时，120分钟
    # 2. 可以redo，带日期格式的，需要带延迟下载，如果不带日期的文件，直接下载，不需要延迟
    # 3. 
        # minute_clock = [m for m in range(0,60,15)]
        # minute_clock
        # [0, 15, 30, 45]
    # """
    
    # hour_space      = num_collect_perday//(24)
    # minute_space    = num_collect_perday//(24*60)
    
    # ####优先按分钟间隔下载
    # if minute_space != 0:
        # task_hour   = '00-23'
        # # minute_list = [m for m in range(0,60,minute_space)]
        # # task_minute = ','.join(minute_list)
        # # task_second = '00'
        # minute_list = [str(m) for m in range(0,60,minute_space)]
        # #print (minute_list)
        # task_minute = ','.join(minute_list)
        # #print (task_minute) 
        # task_second = '00'   
    # if minute_space == 0 and hour_space != 0:
        # hour_list   = [str(h) for h in range(0,24,hour_space)]
        # task_hour   = ','.join(hour_list)
        # task_minute = '00'
        # task_second = '00'           
    
    # return task_hour,task_minute,task_second
    
    
  

# def get_task_hour_minute_second(scheduling_interval_min,scheduling_delayed_min):
    # """
    # 1. 根据每日收集的数据量，来推算启动小时，再取1/12,比如1天下载1个文件，间隔24小时，1/12就是2小时，120分钟
    # 2. 可以redo，带日期格式的，需要带延迟下载，如果不带日期的文件，直接下载，不需要延迟
    # 3. 
        # minute_clock = [m for m in range(0,60,15)]
        # minute_clock
        # [0, 15, 30, 45]
    # """
    
    # ####调度间隔没有00的情况
    # hour_space      = scheduling_interval_min//(60)
    # minute_space    = scheduling_interval_min%(60)
    
    
    # ####优先按分钟间隔下载
    # if minute_space != 0:
        # task_hour   = '00-23'
        # # minute_list = [m for m in range(0,60,minute_space)]
        # # task_minute = ','.join(minute_list)
        # # task_second = '00'
        # minute_list = [str(m) for m in range(0,60,minute_space)]
        # #print (minute_list)
        # task_minute = ','.join(minute_list)
        # #print (task_minute)
        # task_second = '00'
    # if minute_space == 0 and hour_space != 0:
        # hour_list   = [str(h) for h in range(0,24,hour_space)]
        # task_hour   = ','.join(hour_list)
        # task_minute = '00'
        # task_second = '00'           
    
    
    # return task_hour,task_minute,task_second
    
    

def get_download_hour_minute_second(scheduling_interval_min,scheduling_delayed_min):
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
    for scheduling_real in range(0,1440,scheduling_interval_min):
        scheduling_delayed=scheduling_real+scheduling_delayed_min
        ihour=(scheduling_delayed//60)%24
        imin=scheduling_delayed%60
        
        hours.append('%02d'%ihour)
        mins.append('%02d'%imin)

    hours=list(set(hours))
    mins=list(set(mins))
    hours.sort()
    mins.sort()
    
    task_hour=','.join(hours)
    task_minute=','.join(mins)
    task_second = '00'
    
    
    #print('每日调度启动时刻：')
    #print('hour=',task_hour)
    #print('min =',task_min)
    
    return task_hour,task_minute,task_second    
    
    
    
    
def get_product_hour_minute_second(scheduling_interval_min,scheduling_delayed_min,delay_min = 3):
    """
    1. 默认比下载任务推迟5分钟
    """
    
    # 计算调度时间
    hours=[]
    mins=[]
    for scheduling_real in range(0,1440,scheduling_interval_min):
        scheduling_delayed=scheduling_real+scheduling_delayed_min + delay_min
        ihour=(scheduling_delayed//60)%24
        imin=scheduling_delayed%60
        
        hours.append('%02d'%ihour)
        mins.append('%02d'%imin)

    hours=list(set(hours))
    mins=list(set(mins))
    hours.sort()
    mins.sort()
    
    task_hour=','.join(hours)
    task_minute=','.join(mins)
    task_second = '00'
    #task_second = str(delay_second)
    
    #print('每日调度启动时刻：')
    #print('hour=',task_hour)
    #print('min =',task_min)
    
    return task_hour,task_minute,task_second  
    
    
    
def get_alert_hour_minute_second(scheduling_interval_min,scheduling_delayed_min,delay_min = 3):
    """
    1. 默认比下载任务推迟5分钟
    """
    
    # 计算调度时间
    hours=[]
    mins=[]
    for scheduling_real in range(0,1440,scheduling_interval_min):
        scheduling_delayed=scheduling_real+scheduling_delayed_min + delay_min
        ihour=(scheduling_delayed//60)%24
        imin=scheduling_delayed%60
        
        hours.append('%02d'%ihour)
        mins.append('%02d'%imin)

    hours=list(set(hours))
    mins=list(set(mins))
    hours.sort()
    mins.sort()
    
    task_hour=','.join(hours)
    task_minute=','.join(mins)
    task_second = '00'
    #task_second = str(delay_second)
    
    #print('每日调度启动时刻：')
    #print('hour=',task_hour)
    #print('min =',task_min)
    
    return task_hour,task_minute,task_second      
    
    
    
def download_job(searchinfo,exe_path=os.path.dirname(os.path.abspath(__file__)),exe_name = 'download.py'):
    

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
    
    starttime   = (datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S") + datetime.timedelta( minutes=-scheduling_delayed_min)).strftime('%Y%m%d%H%M%S')
    endtime     = starttime


    ####启动任务
    cmd = 'python3' + ' ' + exe_fullpath + ' ' + category_abbr_en + ' ' + starttime + ' ' + endtime
    #print (cmd)
    
    #print (category_abbr_en)
    #print ('task_hour = %s'%task_hour) 
    #print ('task_minute = %s'%task_minute) 
    #print ('task_second = %s'%task_second)     

    
    #print ('任务延迟开始......') 
    #print ('任务延迟 %d秒'%(scheduling_delayed_min*60) )    
    ####启动数据下载任务，加入延迟操作，保证数据下载完整
    #time.sleep(scheduling_delayed_min*60)#延迟下载，单位秒
    #print ('任务延迟结束')
    ####方案1
    #os.system(cmd)
    
    
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
    
    
    # ####数据库监控表入库
    # ####如何更改调度任务表，调度任务表的信息用不用修改，我们最关心的是file_info数据表，调度任务表只是自动调度任务，最终以file_info表收集的信息为主
    # create_time = get_current_BJT()##入库时间按北京时间
    # update_time = get_current_BJT()##入库更新时间按北京时间
    
    # pga=PostgresArchive()
    # config_infos={
                # 'task_name':task_name,
                # 'create_time':create_time,
                # 'update_time':update_time,                
                # 'log':log,
                # 'status':status,
                # 'cmd':cmd,
                # 'data_class':data_class,
                # 'research_area':research_area,
                # 'website':website,
                # 'category_abbr_en':category_abbr_en
                # }
                
    # #pga.insert_db_table(database_name='task_db', table_name='t_task_monitor', config_element = config_infos)
    # #pga.insert_db_table(database_name='yjy015', table_name='task_monitor', config_element = config_infos)
    # pga.insert_db_table(database_name=db_name, table_name=table_name, config_element = config_infos)
    
    
    return
    
    
def redo_download_job(expire_days=3):
   
    """
    1. 每天上午06点开始重做前3天的失败任务,可能很多失败任务,查询log失败和status为False
    2. 格式化输出',\',格式化\加'，因为sql查询日期需要带单引号
    """
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'data_monitor'
    
    current_date    ='\'%s\''%(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    expire_date     ='\'%s\''%((datetime.datetime.now() + datetime.timedelta( days=-expire_days)).strftime("%Y-%m-%d %H:%M:%S"))
    #search_log     = '\'%s\''%'失败'
    search_status   = '\'%s\''%'False'
    #sqlcmd='SELECT * FROM %s WHERE log = %s and status = %s and create_time BETWEEN %s and %s'%(table_name,search_log,search_status,expire_date,current_date)
    #sqlcmd='SELECT * FROM %s WHERE status = %s and create_time BETWEEN %s and %s'%(table_name,search_status,expire_date,current_date)    
    ####2个表联合查询
    sqlcmd="SELECT data_monitor.*, data_category.redo_flag FROM data_monitor INNER JOIN data_category ON data_monitor.category_abbr_en = data_category.category_abbr_en \
            WHERE data_monitor.status = %s and create_time BETWEEN %s and %s"%(search_status,expire_date,current_date)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        #loggings.debug_log(str(e))                   #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())   #输出堆栈异常到log日志里        
        raise Exception(traceback.format_exc())                
    
    
    ####查询到的数据
    if(searchinfos):
        for searchinfo in searchinfos:
            ####传入的数据库记录，解析各个字段
            task_name = searchinfo['task_name']
            create_time = searchinfo['create_time']
            log = searchinfo['log']
            status = searchinfo['status'] 
            cmd = searchinfo['cmd']
            data_class = searchinfo['data_class']    
            research_area = searchinfo['research_area']
            website = searchinfo['website']
            category_abbr_en = searchinfo['category_abbr_en']
            redo_flag = searchinfo['redo_flag']
            
            ####需要添加category_abbr_en种类在data_category表中redo_flag判断,如果是fasle则不需要重做,因为实时更新的数据,重做下载的不是历史数据,而是实时数据
            if('False' == redo_flag):
                continue
            
            ####任务启动时间，使用UTC时间启动，因为网站更新数据的时间是UTC时间
            logStarttime  = get_current_BJT()
            
            ####实例化日志类
            loggings=Loggings(logStarttime,category_abbr_en)
            
            ####方案2
            ####如果异常，可能没有返回值
            ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=None)    
            #ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=1)
            
            """
            1. ret.returncode == 0不能确定下载任务是否完成，需要根据下载任务返回状态信息，一起判别才作为此任务成功的标志
            
            """            
            
            ####需要加入wget下载里，判断是否是重做任务
            #if ret.returncode == 0 and ret.stderr == '' and ret.stdout == '':        
            if ret.returncode == 0:
                update_status = 'True'
                update_log = '成功'
                """ret返回的stdout，把屏幕输出的内容全部赋值给stdout"""
                #print("success:",ret)
                #print("success:",ret)        
            else:
                update_status = 'False'
                ##log只记录成功和失败，失败的详细原因记录到任务日志里
                log = ret.stderr
                #update_log = '失败'      
                loggings.debug_log('ret.returncode = %d'%ret.returncode)#输出hadoop异常操作到log日志里           
                loggings.debug_log(ret.stderr)                          #输出hadoop异常操作到log日志里       
                print("error:",ret.stderr)
            
            
            ####数据库监控表入库
            ####如何更改调度任务表，调度任务表的信息用不用修改，我们最关心的是file_info数据表，调度任务表只是自动调度任务，最终以file_info表收集的信息为主
            update_time = get_current_BJT()##入库时间按北京时间
            pga=PostgresArchive()
            config_infos={
                        'task_name':task_name,
                        'create_time':create_time,
                        'update_time':update_time,                    
                        'log':update_log,
                        'status':update_status,
                        'cmd':cmd,
                        'data_class':data_class,
                        'research_area':research_area,
                        'website':website,
                        'category_abbr_en':category_abbr_en
                        }
                        
            condition_infos={
                            'task_name':task_name,
                            'create_time':create_time,
                            'status':status,                    
                            'log':log}#更新失败的字段
                        
            #pga.insert_db_table(database_name='task_db', table_name='t_task_monitor', config_element = config_infos)
            #pga.update_db_table(database_name='yjy015', table_name='task_monitor', config_element = config_infos, condition_element=condition_infos)
            pga.update_db_table(database_name=db_name, table_name=table_name, config_element = config_infos, condition_element=condition_infos)
            
            
            
    return   
   
   
#def product_job(searchinfo,delay_min = 3):   
def product_job(searchinfo,delay_min):
    
    
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'product_monitor'
    
    
    ####传入的数据库记录，解析各个字段
    category_abbr_en = searchinfo['category_abbr_en']
    category_name_zh = searchinfo['category_name_zh']
    task_name = '产品生产 ' + category_name_zh + ' ' + category_abbr_en
    scheduling_delayed_min  = int(searchinfo['scheduling_delayed_min'])
    
    
    data_class = searchinfo['data_class']
    research_area = searchinfo['research_area']
    website = searchinfo['website']
    
    
    ####任务启动时间，使用UTC时间启动，因为网站更新数据的时间是UTC时间
    task_starttime = get_current_UTC()
    log_starttime  = get_current_BJT()
    
    
    ####调度推迟5分钟，实际下任务的时间，也得推算到5分钟之前的时间
    # starttime = (datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S") + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    # endtime = starttime
    
    ##2020-05-27 15:31格式写入数据库2020-05-27 15:31:00
    ##查找的时候，开始时间，结束时间单位精确到分钟，秒00~59，查找这个范围的数据
    
    year    = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").year
    month   = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").month
    day     = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").day
    hour    = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").hour
    minute  = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").minute
    s_second  = 0
    e_second  = 59


    ####计算延迟下载之前的时刻，精确到分钟，秒00~59范围匹配
    starttime   = (datetime.datetime(year,month,day,hour,minute,s_second) + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    endtime     = (datetime.datetime(year,month,day,hour,minute,e_second) + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    
    
    ####实例化product类
    prd = Product(category_abbr_en,starttime,endtime)

    # if category_abbr_en == 'CDA_DSCOVR_SW':
        # try:
            # prd.product_DSCOVR_FC()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'    
    # if category_abbr_en == 'CDA_DSCOVR_MAG':
        # try:
            # prd.product_DSCOVR_mag()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'   
    if category_abbr_en == 'Ngdc_DSCOVR_SW':
        try:
            prd.product_Ngdc_DSCOVR_SW()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'  
    if category_abbr_en == 'Ngdc_DSCOVR_MAG':
        try:
            prd.product_NGDC_DSCOVR_m1s()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'              
    if category_abbr_en == 'CDA_TIMED_SL2a':
        try:
            prd.product_Timed_L2A()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'
    if category_abbr_en == 'CDA_GPS_TEC':
        try:
            prd.product_IGS_TEC()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'              
    if category_abbr_en == 'JSOC_AIA_0094':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()
            log = str(e)
            status = 'False'    
    if category_abbr_en == 'JSOC_AIA_0131':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()
            log = str(e)
            status = 'False'    
    if category_abbr_en == 'JSOC_AIA_0171':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'        
    if category_abbr_en == 'JSOC_AIA_0193':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'        
    if category_abbr_en == 'JSOC_AIA_0211':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'       
    if category_abbr_en == 'JSOC_AIA_0304':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'        
    if category_abbr_en == 'JSOC_AIA_0305':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'      
    if category_abbr_en == 'JSOC_AIA_1600':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'      
    if category_abbr_en == 'JSOC_AIA_1700':
        try:
            prd.product_SDO_draw_grid()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'    
    if category_abbr_en == 'JSOC_HMI_12m':
        try:
            prd.product_SDO_draw_AR()
            log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            log = str(e)
            status = 'False'           
            
            
    create_time = get_current_BJT()##入库时间按北京时间
    update_time = get_current_BJT()##入库更新时间按北京时间
        
    pga=PostgresArchive()
    config_infos={
                'task_name':task_name,
                'create_time':create_time,
                'update_time':update_time,
                'log':log,
                'status':status,
                'data_class':data_class,
                'research_area':research_area,
                'website':website,
                'category_abbr_en':category_abbr_en
                }
                
    #pga.insert_db_table(database_name='task_db', table_name='t_task_monitor', config_element = config_infos)
    #pga.insert_db_table(database_name='yjy015', table_name='task_monitor', config_element = config_infos)
    pga.insert_db_table(database_name=db_name, table_name=table_name, config_element = config_infos)
    
    
    return
    

#def alert_job(searchinfo,delay_min = 3):   
def alert_job(geomag,electron,flare,proton,searchinfo,delay_min):
    
    
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'alert_monitor'
    
    ####传入的数据库记录，解析各个字段
    category_abbr_en = searchinfo['category_abbr_en']
    category_name_zh = searchinfo['category_name_zh']
    task_name = '事件警报 ' + category_name_zh + ' ' + category_abbr_en
    scheduling_delayed_min  = int(searchinfo['scheduling_delayed_min'])
    
    
    data_class = searchinfo['data_class']
    research_area = searchinfo['research_area']
    website = searchinfo['website']
    
    
    ####任务启动时间，使用UTC时间启动，因为网站更新数据的时间是UTC时间
    task_starttime = get_current_UTC()
    log_starttime  = get_current_BJT()
    

    ####调度推迟5分钟，实际下任务的时间，也得推算到5分钟之前的时间
    # starttime = (datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S") + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    # endtime = starttime
    
    ##2020-05-27 15:31格式写入数据库2020-05-27 15:31:00
    ##查找的时候，开始时间，结束时间单位精确到分钟，秒00~59，查找这个范围的数据
    
    year    = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").year
    month   = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").month
    day     = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").day
    hour    = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").hour
    minute  = datetime.datetime.strptime(task_starttime, "%Y-%m-%d %H:%M:%S").minute
    s_second  = 0
    e_second  = 59
    
    
    ####计算延迟下载之前的时刻，精确到分钟，秒00~59范围匹配
    starttime   = (datetime.datetime(year,month,day,hour,minute,s_second) + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    endtime     = (datetime.datetime(year,month,day,hour,minute,e_second) + datetime.timedelta( minutes=-(scheduling_delayed_min+delay_min))).strftime('%Y-%m-%d %H:%M:%S')
    
    
    ####实例化product类
    alert = Alert(geomag,electron,flare,proton,category_abbr_en,starttime,endtime)
    
    
    ####判断数据种类，根据数据种类的启动时刻，来启动相应的警报任务
    ####Kp指数使用SWPC,SWPC_latest_DGD; 不使用德国GFZ,GFZ_Kp_web
    #if category_abbr_en == 'GFZ_Kp_web' or category_abbr_en == 'SWPC_latest_DGD':    
    if category_abbr_en == 'SWPC_latest_DGD':
        alert_type = 'geomag_storm_docx'
        #loggings=Loggings(log_starttime,'alert_' + category_abbr_en)#实例化日志类    
        #loggings.debug_log('SWPC_latest_DGD')
        
        try:
            alert.alert_geomag_storm()
            monitor_log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            monitor_log = str(e)
            #loggings.debug_log(traceback.format_exc())              #输出堆栈异常到log日志里             
            status = 'False'    
    
    if category_abbr_en == 'SWPC_GOES_IE5m':
        alert_type = 'electron_burst_docx'
        #loggings=Loggings(log_starttime,'alert_' + category_abbr_en)#实例化日志类          
        try:
            alert.alert_electron_burst()
            monitor_log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            monitor_log = str(e)
            #loggings.debug_log(traceback.format_exc())              #输出堆栈异常到log日志里             
            status = 'False'    

    if category_abbr_en == 'SWPC_GOES_XR1m':
        alert_type = 'solar_flare_docx'   
        #loggings=Loggings(log_starttime,'alert_' + category_abbr_en)#实例化日志类            
        try:
            alert.alert_solar_flare()
            monitor_log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            monitor_log = str(e)
            #loggings.debug_log(traceback.format_exc())              #输出堆栈异常到log日志里             
            status = 'False'   
            
    if category_abbr_en == 'SWPC_GOES_IP5m':
        alert_type = 'solar_proton_docx'
        #loggings=Loggings(log_starttime,'alert_' + category_abbr_en)#实例化日志类           
        try:
            alert.alert_solar_proton()
            monitor_log = '成功'
            status = 'True'            
        except Exception as e:
            #log = traceback.format_exc()        
            monitor_log = str(e)
            #loggings.debug_log(traceback.format_exc())      #输出堆栈异常到log日志里            
            status = 'False'   

        # alert_type = 'geomag_storm_docx'
        # try:
            # alert.alert_geomag_storm()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'    
    

        # alert_type = 'electron_burst_docx'
        # try:
            # alert.alert_electron_burst()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'    


        # alert_type = 'solar_flare_docx'    
        # try:
            # alert.alert_solar_flare()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'   


        # alert_type = 'solar_flare_docx'
        # try:
            # alert.alert_solar_flare()
            # log = '成功'
            # status = 'True'            
        # except Exception as e:
            # #log = traceback.format_exc()        
            # log = str(e)
            # status = 'False'   

            
    create_time = get_current_BJT()     ##入库时间按北京时间
    update_time = get_current_BJT()     ##入库更新时间按北京时间
    
    pga=PostgresArchive()
    config_infos={
                'task_name':task_name,
                'create_time':create_time,
                'update_time':update_time,
                'log':monitor_log,
                'status':status,
                'alert_type':alert_type   ##录入事件类型，不是数据来源类型
                }
                
    pga.insert_db_table(database_name=db_name, table_name=table_name, config_element = config_infos)
    
    return
    
    
    
    
def migrate_log_job(current_rootpath=os.path.dirname(os.path.abspath(__file__))):
    """
    1. 日志迁移任务，每天的23:55分钟，把当天的所有任务日志迁移到当天的log日期文件夹里
    2. 特殊情况，如果断网，导致任务失败，导致程序，需要重新启动，导致积累的很长时间的日志，都写入任务启动当天的日期文件夹里
    3. 每天的任务日期，迁移时间按UTC任务，23：55分钟，积累了1天的日志，BJT大概是第2天的07：55分钟，收集UTC 整天的任务日志
    
    """
        
    yyyy_mm_dd = datetime.datetime.now().strftime('%Y-%m-%d')    
    logpath = os.path.join(current_rootpath,'logger','log',yyyy_mm_dd)
    #print ('logpath = %s'%logpath)
    
    ####拷贝迁移当天的日志
    shutil.copy(os.path.join(current_rootpath,'apscheduler.log'),logpath)
    shutil.copy(os.path.join(current_rootpath,'automatically_task.log'),logpath)
    
    
    ####移动当天的日志
    ####实际测试发现，移动日志，不影响日志追加，所以不能移动，只能拷贝
    #shutil.move(os.path.join(current_rootpath,'apscheduler.log'),logpath)
    #shutil.move(os.path.join(current_rootpath,'automatically_task.log'),logpath)    
    
    ####删除日志
    os.remove(os.path.join(current_rootpath,'apscheduler.log'))
    os.remove(os.path.join(current_rootpath,'automatically_task.log'))

    
    ####新建当天的日志
    cmd1 = 'touch %s'% os.path.join(current_rootpath,'apscheduler.log')
    cmd2 = 'touch %s'% os.path.join(current_rootpath,'automatically_task.log')
    os.system(cmd1)
    os.system(cmd2)
    
    return
    
    
    
    

def clean_dirs(srcpath=os.path.join(os.path.dirname(os.path.abspath(__file__)),'logger','log',''),expire_day=90):
    """
    1. 不能按文件夹日期比较，按文件的日期比较，因为前72小时的文件在文件夹里
    2. 可以定时删除，删除的时间点，定00：00：00，比如2020-04-22 00：00：00 ，前4天的时间2020-04-18 00：00：00
    3. 删除年月日文件夹，遍历比较即可，然后os.walk，删除年月日文件夹
   
    """

    expire_yyyymmdd  =  (datetime.datetime.now() + datetime.timedelta(days=-expire_day)).strftime('%Y%m%d')
    
    ##遍历文件夹
    for root, dirs, files in os.walk(srcpath):
        #print (root,dirs)
        for dir in dirs:
            ##空文件夹，自动跳出
            ##以下判断有bug,比如*/202004/20200421,202004目录小于20200421，所以会把202004目录下所有的文件夹都删除
            ##字符串按位比较，两个字符串第一位字符的ascii码谁大，字符串就大，不再比较后面的
            ##增加过滤，筛选文件夹
            ##文件夹是数字，文件夹长度为8，文件夹日期小于过期日期
            try:
                datetime.datetime.strptime(dir, '%Y-%m-%d')
            except Exception as e:
                ####遍历文件夹，不是日期格式返回
                continue
            
            ####如果是日期格式，转换格式，比较日期大小
            dir_yyyymmdd = datetime.datetime.strptime(dir, '%Y-%m-%d').strftime('%Y%m%d')
            if (dir_yyyymmdd <= expire_yyyymmdd ):   
                print ('删除', root, dir)
                shutil.rmtree(os.path.join(root, dir))

    return
    
    
    
    
def kill_process():
    """
    1. 每天查杀当天的sk_wait_data 进程，UTC=12点, BJT=20点
    """
    
    cmd = 'sh /home/YJY015/code/status_task.sh'
    ####管道调用
    ####如果异常,可能没有返回值
    ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=None)       
    print (cmd)
    
    return 
    
    
    
def scan_job():
    """
    1. 扫描配置表,如果用户修改了data_category表, 保证每个任务，都能及时的读取里面新增的记录
    2. 保证下载任务能每次启动，都能读取最新的data_category表信息
    
    """    
    #### 读取任务数据库配置信息
    pga=PostgresArchive()
    db_name = configs['db_name'] 
    table_name  = 'data_category'
    searchinfos=pga.search_db_table_usercmd(database_name=db_name,sqlcmd='select * from %s' % table_name)        
    
    return searchinfos
    
    
def listener(event):
    if event.exception:
        print ('The job crashed :(')
    else:
        print ('The job worked :)')
        
        
def log_setting(logpath=os.path.dirname(os.path.abspath(__file__))):
    logname=os.path.join(logpath,'apscheduler.log')
    
    # user_name = get_username()
    # host_name = get_hostname()
    # dic = {'user_name':user_name,
           # 'host_name':host_name}
    #log_format = "[%(user_name)s][%(asctime)s][%(process)10d]:  %(message)s"             
    #log_format = "[%(asctime)s][%(process)10d]:  %(message)s"
    log_format = "[%(asctime)s]:  %(message)s"    
    logging.basicConfig(level=logging.INFO,
                        filename=logname,
                        filemode='a',
                        #format='%(asctime)s %(message)s',      ##''里的[]是信息输出，加的'[%(asctime)s %(message)s]'可以去掉
                        format=log_format,
                        datefmt='%Y-%m-%d %H:%M:%S'             ##默认输出格式带毫秒'%Y-%m-%d %H:%M:%S%p'
                        )
    return logging
    
    
    
    
if __name__ == '__main__':
        
    #### 读取任务数据库配置信息
    pga=PostgresArchive()
    
    #db_name = 'yjy015'
    db_name     = configs['db_name'] 
    table_name  = 'data_category'
    #searchinfos=pga.search_db_table_usercmd(database_name='task_db',sqlcmd='select * from %s' % table_name)
    searchinfos=pga.search_db_table_usercmd(database_name=db_name,sqlcmd='select * from %s' % table_name)    
    
    
    ####产品生产列表
    ####CDA_DSCOVR_SW，CDA_DSCOVR_MAG网站停止更新，不需要下载
    ####新增Ngdc_DSCOVR_SW，Ngdc_DSCOVR_MAG
    product_list = ['Ngdc_DSCOVR_SW','Ngdc_DSCOVR_MAG','CDA_TIMED_SL2a','CDA_GPS_TEC',
                    'JSOC_AIA_0094','JSOC_AIA_0131','JSOC_AIA_0171','JSOC_AIA_0193',
                    'JSOC_AIA_0211','JSOC_AIA_0305','JSOC_AIA_1600','JSOC_AIA_1700',
                    'JSOC_HMI_12m']
    
    ####product产品绘图,需要依赖data文件下载,保证data文件下载并入库完成,再启动product产品生产,需要添加时间延迟,保证文件下载完成,单位是分钟
    product_delay_list  = { 
                            'Ngdc_DSCOVR_SW':180,
                            'Ngdc_DSCOVR_MAG':180,
                            'CDA_TIMED_SL2a':180,
                            'CDA_GPS_TEC':180,   #延迟1个月零33分钟开始下载43233，下载耗时 5分钟10秒
                            'JSOC_AIA_0094':180, #下载延迟66分钟,下载耗时60分钟,实际下载耗时4分钟
                            'JSOC_AIA_0131':180,
                            'JSOC_AIA_0171':180,
                            'JSOC_AIA_0193':180,
                            'JSOC_AIA_0211':180,
                            'JSOC_AIA_0305':180,
                            'JSOC_AIA_1600':180,
                            'JSOC_AIA_1700':180,
                            'JSOC_HMI_12m':180}
        
    ####事件警报列表
    alert_list = ['SWPC_latest_DGD','SWPC_GOES_XR1m','SWPC_GOES_IP5m','SWPC_GOES_IE5m']
    ####alert警报,需要依赖物理要素入库,保证物理要素入库完成,再启动alert产品生产,需要添加延迟,单位是分钟
    alert_delay_list  = {   'SWPC_latest_DGD':1, #间隔5分钟下载1次,1分钟的下载时间;网站实际更新2020-06-28 17:45:20	2020-06-28 09:00:00	SWPC_latest_DGD,延迟45分钟
                            'SWPC_GOES_XR1m':0,
                            'SWPC_GOES_IP5m':0,  #间隔5分钟下载1次,实际显示10秒钟下载完成;实际网站更新延迟10分钟;2020-06-28 17:35:12更新2020-06-28 09:25:00
                            'SWPC_GOES_IE5m':1}
                            
    #### 启动定时任务
    #scheduler = BlockingScheduler()     #阻塞方式
    #scheduler = BackgroundScheduler()   #非阻塞方式
    
    #### # 20个线程，5个进程
    #### executors 命名关键字不能冲突
    executor = {'default': ThreadPoolExecutor(200),'processpool': ProcessPoolExecutor(200)}
    ##30秒的任务超时容错,0-30秒范围内,启动
    ##每天的UTC=23：00：00，BJT=07:00:00开始查杀死掉的进程，查杀一次
    ##max_instances每个任务最多同时触发次数
    job_default = {'coalesce': True,'max_instances':96,'misfire_grace_time':30}
                    
    
    #executor = ThreadPoolExecutor(max_workers=200)
    #scheduler = BlockingScheduler(executors={'default': executor})                 #阻塞方式
    scheduler = BlockingScheduler(executors=executor,job_defaults=job_default)      #阻塞方式    
     
    #### 用户添加用例add_job
    ####方案1，手动添加任务
    #job1 = scheduler.add_job(func=scheduler_job,args=['CDA_TIMED_SL2b'], trigger='cron', hour='9',minute='45',timezone=pytz.utc,id='CDA_TIMED_SL2b')  ##每天的00时开始执行
    #job2 = scheduler.add_job(func=scheduler_job,args=['IGG_GEOMAGhour_BM'], trigger='cron', hour='9',minute='06',timezone=pytz.utc,id='IGG_GEOMAGhour_BM')  ##每天的00时开始执行
    
    
    ####每天定时查询最近3天的失败任务,北京时间 08：00-18:00上班，间隔12小时
    ####UTC 01,13       BJT 09,21
    job = scheduler.add_job(func=redo_download_job, args=[3], trigger='cron', hour='01,13', timezone=pytz.utc, id='redo_download_job')
    
    
    ####每天定时迁移程序日志和调度日志
    ####日志可以迁移,可以拷贝; 但是不能删除原来被追加的文件
    #job = scheduler.add_job(func=migrate_log_job,trigger='cron', hour='23',minute = '55', timezone=pytz.utc, id='migrate_log_job')
    
    
    ####每天23:55(北京时间),清理过期日期文件夹
    job = scheduler.add_job(func=clean_dirs, trigger='cron', hour='23', minute = '55', id='clean_dirs')
    
    ####每天20:00(北京时间),清理sk_wait_data 进程
    job = scheduler.add_job(func=kill_process, trigger='cron', hour='20', minute = '00', id='kill sk_wait_data 进程')
    
    
    ####方案2，从数据库查询，并添加任务
    for searchinfo in searchinfos:
        #pass
        category_name_zh        = searchinfo['category_name_zh']
        # task_triggers = searchinfo['task_triggers']
        # task_hour = searchinfo['task_hour']
        # task_minute = searchinfo['task_minute']
        # task_second = searchinfo['task_second']
        num_collect_perday      = int(searchinfo['num_collect_perday'])
        scheduling_interval_min = int(searchinfo['scheduling_interval_min'])
        scheduling_delayed_min  = int(searchinfo['scheduling_delayed_min'])
        category_abbr_en        = searchinfo['category_abbr_en']
        website_status          = searchinfo['website_status']
        redo_flag               = searchinfo['redo_flag']
        
        
        ####变量合法性处理,针对用户自定义添加的网站
        if scheduling_interval_min <= 0:
            scheduling_interval_min = 1
            
            
        ####第1步，先判断网站有效性，如果网站状态停止更新,则此任务不需要启动
        ####网站停止更新,网站产出的data,product,alert等产品都跳过
        if('False' == website_status):
            continue
            
        #########################数据收集下载任务###############################
        ####解析任务启动时刻
        task_hour,task_minute,task_second = get_download_hour_minute_second(scheduling_interval_min,scheduling_delayed_min)
        idname = '数据收集 ' + category_name_zh + ' ' + category_abbr_en
        ####添加任务
        #job = scheduler.add_job(func=scheduler_job, args=[category_abbr_en], trigger='cron', hour=task_hour, minute=task_minute, timezone=pytz.utc, id=task_name)
        #job = scheduler.add_job(func=scheduler_job, args=[searchinfo], trigger='cron', hour=task_hour, minute=task_minute, timezone=pytz.utc, id=task_name)
        #job = scheduler.add_job(func=scheduler_job, args=[searchinfo], trigger=task_triggers, hour=task_hour, minute=task_minute, timezone=pytz.utc, id=task_name)
        #job = scheduler.add_job(func=scheduler_job, args=[searchinfo], trigger='cron', hour=task_hour, minute=task_minute, second=task_second, timezone=pytz.utc, id=category_name_zh)
        job = scheduler.add_job(func=download_job, args=[searchinfo], trigger='cron', hour=task_hour, minute=task_minute, second=task_second, timezone=pytz.utc, id=idname)        
        
        
        #########################产品生产任务###############################
        delay_min = 3
        if category_abbr_en in product_delay_list:
            #print (delay_list[category_abbr_en])
            #delay_min = 6*60#360分钟,实际测试,下载速度很慢
            delay_min = product_delay_list[category_abbr_en]
            
                        
        task_hour,task_minute,task_second = get_product_hour_minute_second(scheduling_interval_min,scheduling_delayed_min,delay_min)
        idname = '产品生产 ' + category_name_zh + ' ' + category_abbr_en        ##id不能重复，所以需要加限制区分
        ##产品生产
        if category_abbr_en in product_list:
            job = scheduler.add_job(func=product_job, args=[searchinfo,delay_min], trigger='cron', hour=task_hour, minute=task_minute, second=task_second, timezone=pytz.utc, id=idname)        


        #########################事件预警任务###############################        
        ##事件警报,保证数据下载时间+入库时间,小于2分钟,指标要求2分钟
        delay_min = 2
        if category_abbr_en in alert_delay_list:
            #print (delay_list[category_abbr_en])
            #delay_min = 6*60#360分钟,实际测试,下载速度很慢
            delay_min = alert_delay_list[category_abbr_en]
            
        task_hour,task_minute,task_second = get_alert_hour_minute_second(scheduling_interval_min,scheduling_delayed_min,delay_min)        
        idname = '事件警报 ' + category_name_zh + ' ' + category_abbr_en        ##id不能重复，所以需要加限制区分        
        
        ####4个实例化警报事件，只能在启动脚本时候，启动一次
        current_starttime = get_current_UTC()   ##当前时刻的UTC
        yesterday_starttime = get_yesterday_UTC()

        year    = datetime.datetime.strptime(current_starttime, "%Y-%m-%d %H:%M:%S").year
        month   = datetime.datetime.strptime(current_starttime, "%Y-%m-%d %H:%M:%S").month
        day     = datetime.datetime.strptime(current_starttime, "%Y-%m-%d %H:%M:%S").day
        hour    = datetime.datetime.strptime(current_starttime, "%Y-%m-%d %H:%M:%S").hour
        minute  = datetime.datetime.strptime(current_starttime, "%Y-%m-%d %H:%M:%S").minute
        
        ##计算，每类事件的初始化启动时刻，向下取整
        hour_geomag        = hour//3*3##如果hour是2,导致计算的hour都是0,导致下面的hour本来是2,结果也当0处理
        #hour = hour//3*3 - 6 #临时测试,向下取整,减去x小时   
        geomag      =   event_alert_opt.geomag_storm.Geomag_strom(year,month,day,hour_geomag)          ##3小时1次，启动查找最近3小时的时刻作为初始值
        
        hour_electron = hour//1*1
        electron    =   event_alert_opt.electron_burst.Electron_burst(year,month,day,hour_electron,0)    ##1小时1次，启动查找最近1小时的时刻作为初始值
        
        #minute=minute//5*5
        minute_flare = minute//1*1      
        flare       =   event_alert_opt.solar_flare.Solar_flare(year,month,day,hour,minute_flare)     ##5分钟1次，启动查找最近5小时的时刻作为初始值
        
        minute_proton = minute//5*5        
        proton      =   event_alert_opt.solar_proton.Solar_proton(year,month,day,hour,minute_proton)   ##5分钟1次，启动查找最近5小时的时刻作为初始值
        
        if category_abbr_en in alert_list:
            job = scheduler.add_job(func=alert_job, args=[geomag,electron,flare,proton,searchinfo,delay_min], trigger='cron', hour=task_hour, minute=task_minute, second=task_second, timezone=pytz.utc, id=idname)        
        
        
    #### 监听任务
    #scheduler.add_listener(listener,EVENT_JOB_EXECUTED|EVENT_JOB_ERROR)
    
    
    #### 任务日志
    logging = log_setting()
    scheduler._logger = logging
    
    
    #### 启动任务，只能启动1次，不可以重复启动
    try:
        print('begin start......')
        ##start阻塞
        scheduler.start()
        print ('end start......')
    except Exception as e:
        exit(str(e))
    
    