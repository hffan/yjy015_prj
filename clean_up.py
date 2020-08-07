#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
@user guide
1. 删除数据 cd /home/YJY015/code;python3 /home/YJY015/code/clean_up.py 2020-07-05 2020-07-05 data_file_info
2. 删除产品 cd /home/YJY015/code;python3 /home/YJY015/code/clean_up.py 2020-07-05 2020-07-05 product_file_info
                    
@modify history
1. 实际测试发现只有cleanup_data.log,没有cleanup_product.log文件
                    
"""


import os
import sys
import datetime
import traceback

from db.postgres_table import *
from db.postgres_archive import *


from logger.logger import *
from io_interface.io_stat import *


from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_current_BJT
from cfg.conf import *



def record_db(clean_up_tablename,record_time,update_time,start_time,end_time,status):
    db_name = configs['db_name']
    table_name  = 'clean_up_monitor'    
    pga=PostgresArchive()
    config_infos={
                'table_name':clean_up_tablename,
                'record_time':record_time,
                'update_time':update_time,                
                'start_time':start_time,
                'end_time':end_time,
                'status':status}
    pga.insert_db_table(db_name,table_name,config_infos)    
    return


def update_db(config_infos,condition_infos):
    db_name     = configs['db_name']
    table_name  = 'clean_up_monitor'    
    pga         =PostgresArchive()  
    pga.update_db_table(db_name,table_name,config_infos,condition_infos) 
    return
    
        
def check_db(clean_up_tablename,start_time,end_time):
    """
    1. 首先,查询数据库,查看是否之前删除过数据,有删除记录
    2. 如果status=True说明之前删除成功,这次删除就是多余操作,直接return结束程序
    3. 如果status=False说明之前的程序没有删除,或者删除中途出错,或者删除之后,没有入库导致status为False,这种情况,需要再运行一次删除,并更改status的状态
    4. 如果status查询失败,说明之前没有进行删除操作,这次需要重新录入初始化status状态,删除数据,更改status状态为True
    5. 如果数据库中不存在data,product产品数据,也需要update,status的状态为True,也认为此次操作顺利完成,否则前端读status状态为false,认为删除操作一直进行
    """
    db_name     =   configs['db_name']
    table_name  =   'clean_up_monitor'
    pga         =   PostgresArchive() 
     
    sqlcmd="SELECT * FROM %s WHERE table_name = '%s' and start_time = '%s' and end_time = '%s'"%(table_name,clean_up_tablename,start_time,end_time)
    searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)
    
    #数据库不为空
    if(searchinfos):
        for searchinfo in searchinfos:                
            status = searchinfo['status']               
            if ('True'==status):                       
                return 0
            if ('False'==status):                       
                return 1                
    else:
        return 2        


def cleanup_data(startime,endtime):
    """
    startime格式最好是 2020-05-27
    endtime 格式最好是 2020-05-27
    
    去数据库中查找，默认是每天的24小时的数据
    startime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找

    """
    
    s_year    = datetime.datetime.strptime(startime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(startime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(startime, "%Y-%m-%d").day
    s_hour    = 0
    s_minute  = 0
    s_second  = 0        
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59       
    # search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    # search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    search_starttime='%s'%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='%s'%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')    
    ####监控初始化状态
    clean_up_tablename='data_file_info'
    start_time=search_starttime
    end_time=search_endtime
    ret_code=check_db(clean_up_tablename,start_time,end_time)
    if 0==ret_code:
        print ('之前有过此时间段的删除操作,不需要再进行删除操作')
        return ##之前有过此时间段的删除操作,不需要再进行删除操作
    if 1==ret_code:
        print ('之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作')
        pass ##之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作
    if 2==ret_code:
        print ('之前没有此时间段的删除操作,需要插入初始状态记录')
        record_time  = get_current_BJT()   
        update_time  = get_current_BJT()  
        status='False'        
        record_db(clean_up_tablename,record_time,update_time,start_time,end_time,status) ##之前没有此时间段的删除操作,需要插入初始状态记录      
    
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'cleanup_data')

    input_rootpath             = configs['rootpath']  
    db_name = configs['db_name'] 
    table_name  = 'data_file_info'
    
    sqlcmd="SELECT * FROM %s WHERE start_time BETWEEN '%s' and '%s'"%(table_name,search_starttime,search_endtime)
    print (sqlcmd)
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            path        = searchinfo['path']
            filename    = searchinfo['filename']
            absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            absolute_path_list.append(absolute_input_fullfilename)  
    
            ####删除表记录
            pga.delete_table_record(db_name,table_name,searchinfo)            
    
    else:
        infos = '数据库 %s,产品不存在,不需要删除时间段: %s %s'%(table_name,startime,endtime)
        loggings.debug_log(infos)#输出log日志里
        ####更改监控状态
        update_time  = get_current_BJT()     
        config_infos={
                    'update_time':update_time,
                    'status':'True'}#配置更新之后的值
        condition_infos={             
                    'start_time':start_time,
                    'end_time':end_time,
                    'status':'False'}    
        update_db(config_infos,condition_infos)        
        return 
        #exit(0)##exit导致整个主程序退出,导致下面调用的子程序跳过
    
    infos = '数据库表data_file_info 记录%d条'%len(searchinfos)
    loggings.debug_log(infos)#输出log日志里    
    
    
    for datafile in absolute_path_list:
        ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
        if not os.path.exists(datafile):
            pass
        else:
            os.remove(datafile)        
    infos = '数据清理完毕.'
    loggings.debug_log(infos)#输出log日志里
   
   
    ####更改监控状态
    update_time  = get_current_BJT()     
    config_infos={
                'update_time':update_time,
                'status':'True'}#配置更新之后的值
    condition_infos={             
                'start_time':start_time,
                'end_time':end_time,
                'status':'False'}    
    update_db(config_infos,condition_infos)
    
   
    return 
    
    
def cleanup_product(startime,endtime):
    """
    startime格式最好是 2020-05-27
    endtime 格式最好是 2020-05-27
    
    去数据库中查找，默认是每天的24小时的数据
    startime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    """

    s_year    = datetime.datetime.strptime(startime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(startime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(startime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59      
    # search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    # search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    search_starttime='%s'%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='%s'%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')    
    ####监控初始化状态
    clean_up_tablename='product_file_info'
    start_time=search_starttime
    end_time=search_endtime
    ret_code=check_db(clean_up_tablename,start_time,end_time)
    if 0==ret_code:
        print ('之前有过此时间段的删除操作,不需要再进行删除操作')
        return ##之前有过此时间段的删除操作,不需要再进行删除操作
    if 1==ret_code:
        print ('之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作')
        pass ##之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作
    if 2==ret_code:
        print ('之前没有此时间段的删除操作,需要插入初始状态记录')
        record_time  = get_current_BJT()   
        update_time  = get_current_BJT()  
        status='False'        
        record_db(clean_up_tablename,record_time,update_time,start_time,end_time,status) ##之前没有此时间段的删除操作,需要插入初始状态记录   

        
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'cleanup_product')

    input_rootpath              = configs['rootpath']         
    db_name                     = configs['db_name'] 
    table_name                  = 'product_file_info'
    
    sqlcmd="SELECT * FROM %s WHERE start_time BETWEEN '%s' and '%s'"%(table_name,search_starttime,search_endtime)
    print (sqlcmd)
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            path        = searchinfo['path']
            filename    = searchinfo['filename']
            absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            absolute_path_list.append(absolute_input_fullfilename)  
    
            ####删除表记录
            pga.delete_table_record(db_name,table_name,searchinfo)            
    
    else:
        infos = '数据库 %s,产品不存在,不需要删除时间段: %s %s'%(table_name,startime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #exit(0)
        ####更改监控状态
        update_time  = get_current_BJT()     
        config_infos={
                    'update_time':update_time,
                    'status':'True'}#配置更新之后的值
        condition_infos={             
                    'start_time':start_time,
                    'end_time':end_time,
                    'status':'False'}    
        update_db(config_infos,condition_infos)        
        return
    
    infos = '数据库表product_file_info 记录%d条'%len(searchinfos)
    loggings.debug_log(infos)#输出log日志里    
    
    
    for datafile in absolute_path_list:
        ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
        if not os.path.exists(datafile):
            pass
        else:
            os.remove(datafile)        
    infos = '产品数据清理完毕.'
    loggings.debug_log(infos)#输出log日志里
    
    
    ####更改监控状态
    update_time  = get_current_BJT()     
    config_infos={
                'update_time':update_time,
                'status':'True'}#配置更新之后的值
    condition_infos={             
                'start_time':start_time,
                'end_time':end_time,
                'status':'False'}    
    update_db(config_infos,condition_infos)
    
    return 
    
    
    
    
if __name__ == "__main__":
    if (len(sys.argv) == 4):
        argv0 = sys.argv[0]
        argv1 = sys.argv[1]#开始时间，格式2020-07-05
        argv2 = sys.argv[2]#结束时间，格式2020-07-05
        argv3 = sys.argv[3]#data_file_info代表删除data,product_file_info代表删除product
        
        
        if argv3 == 'data_file_info':
            try:
                ####删除data
                cleanup_data(argv1,argv2)
            except Exception as e:
                ##如果异常,UI界面如何获取异常
                raise Exception(traceback.format_exc())   
        if argv3 == 'product_file_info':       
            try:
                ####删除product
                cleanup_product(argv1,argv2)            
            except Exception as e:
                ##如果异常,UI界面如何获取异常
                raise Exception(traceback.format_exc())           
        