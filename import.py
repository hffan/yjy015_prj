#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@user guide
2020-06-01 10:28:15
                    1. 测试数据导入功能，cd /home/YJY015/code; python3 import.py /home/YJY015/import/2020-07-14.zip
                    2. 解压，解析下一级目录下的jason配置文件信息，扫描下一级目录文件结构，可以根据jasion的信息匹配，扫描，然后录入数据库
                    3. 数据库表名和外网一致，数据库名更改为yjy015_1
                            
2020-06-11 14:51:32
                    1. 数据库先查，存在就更新数据库，只更新record_time即可,因为其它字段都是作为查询条件，存在说明数据库中的字段一致，更新其它字段是多余的操作;
                    2. 数据库先查，不存在就插入数据库记录;
                    3. 数据解压覆盖，不影响数据个数，而且如果数据名称一样，但是想更新之前的同名数据，可以覆盖;
2020-07-14 10:01:06
                    1. 导入,需要后清理; 导入后清理,下一次导入相同文件名的文件,不需要覆盖操作,因为上一次导入后已经做了清除
                       因为java需要先从本地目录上传到/home/YJY015/import目录,然后调用python import.py脚本,如果import.py先清理导致文件不存在,无法获取文件路径
                    2. 光盘4.7GB,优质光盘8GB，导出不要超过4GB
                    
2020-07-15 12:25:58
                    1. 导入功能中,import_monitor表,目前只有后端定位问题做记录,前端目前没有去status字段来判断是否结束
                    2. 前端根据后端import完成,前端自动结束
2020-07-15 14:05:16
                    1. 导入功能,json文件需要根据导入的当前时间建立时间戳文件夹,保证2个用户同时操作,不会在同一路径下有相同的json文件,导致覆盖
                    2. 如果导入和导出的json文件同名,可能在同一路径下有冲突,需要
                    3. import_monitor表,status状态,如果更新,不论是true，false，都需要更新，updatetime更新为入库的时间
                    4. select *,更改为select count(*) ，提高数据库查询效率
                    5. for循环更改为map，提高执行效率
2020-07-23 13:36:07
                    1. data_file_info表里增加category_abbr_en字段
2020-07-23 15:54:35
                    1. 增加import路径,导入之后，import路径合法性判断，不存在就创建
2020-08-06 16:38:52
                    1. import_monitor表,bool类型更改为int2类型，1,2,3，1是失败，2是导入中，3是成功,4更新中
                    
                    
                    
"""


import os
import sys
import datetime
import traceback
import shutil

from db.postgres_table import *
from db.postgres_archive import *

from logger.logger import *
from io_interface.io_stat import *

from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_current_BJT
from cfg.conf import *
import interact_opt.zipCompressLst

import json
import zipfile




def insert_db(table_name,config_infos):
    """
    1. 插入数据库记录 
    """
    db_name = configs['db_name']
    #table_name  = 'data_file_info'

    pga=PostgresArchive()
    # config_infos={
                # 'category_id':self.db_category_id,
                # 'filename':self.db_filename,
                # 'path':self.db_path,
                # 'record_time':self.db_record_time,
                # 'start_time':self.db_start_time,
                # 'end_time':self.db_end_time,
                # 'file_size':self.db_file_size,
                # 'state':self.db_state,
                # 'log':self.db_log,
                # 'element_storage_status':self.db_element_storage_status}
    #pga.insert_db_table('file_info_db','file_info',config_infos)
    pga.insert_db_table(db_name,table_name,config_infos)
    return
    
    
def search_db(sqlcmd):
    """
    1. 查找数据库,校验是否存在入库数据记录
    2. 如果数据库为空，需要插入；如果数据库不为空，直接更新;
    
    """
    #db_name     = 'yjy015'
    db_name = configs['db_name']
    #table_name  = 'data_file_info'

    pga=PostgresArchive() 
    # f_print('检查数据库,是否存在下载文件......')

    ####方案2，
    #search_name = check_name
    #sqlcmd="SELECT * FROM %s WHERE category_id = %s and filename = '%s'"%(table_name,self.db_category_id,search_name)
    searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)
    
    
    #数据库不为空
    if(searchinfos):
        ####数据库存在count字段,而且为0，则证明数据库中记录为空
        if 'count' in searchinfos[0].keys() and '0'==searchinfos[0]['count']:
            return 2
        else:
            return 1
    else:
        return 2
        
        
def check_db(start_time,end_time):
    """
    1. 首先,查询数据库,查看是否之前删除过数据,有删除记录
    2. 如果status=True说明之前删除成功,这次删除就是多余操作,直接return结束程序
    3. 如果status=False说明之前的程序没有删除,或者删除中途出错,或者删除之后,没有入库导致status为False,这种情况,需要再运行一次删除,并更改status的状态
    4. 如果status查询失败,说明之前没有进行删除操作,这次需要重新录入初始化status状态,删除数据,更改status状态为True
    5. 如果数据库中不存在data,product产品数据,也需要update,status的状态为True,也认为此次操作顺利完成,否则前端读status状态为false,认为删除操作一直进行
    """
    db_name     =   configs['db_name']
    table_name  =   'import_monitor'
    pga         =   PostgresArchive() 
     
    sqlcmd="SELECT * FROM %s WHERE start_time = '%s' and end_time = '%s'"%(table_name,start_time,end_time)
    searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)
    #print(sqlcmd)
    #数据库不为空
    if(searchinfos):
        for searchinfo in searchinfos:                
            status = searchinfo['status']               
            if ('3'==status):                       
                return 0
            if ('1'==status) or ('2'==status):                       
                return 1                
    else:
        return 2   
    
    
#def update_db(config_infos,condition_infos):    
def update_db(table_name,config_infos,condition_infos):
    """
    1. 更新数据库记录
    """
    #db_name     = 'yjy015'
    db_name = configs['db_name']
    #table_name  = 'import_monitor'       
    #table_name  = 'data_file_info'    
    pga=PostgresArchive()   
    pga.update_db_table(db_name,table_name,config_infos,condition_infos) 


def record_db(record_time,update_time,start_time,end_time,status,filesize):
    db_name = configs['db_name']
    table_name  = 'import_monitor'
    pga=PostgresArchive()
    config_infos={
                'record_time':record_time,
                'update_time':update_time,
                'start_time':start_time,
                'end_time':end_time,
                'status':status,
                'filesize':filesize}
    pga.insert_db_table(db_name,table_name,config_infos)    
    return
    
    
def record_data(db_record):
    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    """
    table_name = 'data_file_info'    
    #print ('into data_file_info record import....')
    
    # input()
    
    category_id = db_record['category_id']
    category_abbr_en = db_record['category_abbr_en']
    filename    = db_record['filename']
    path        = db_record['path']
    start_time  = db_record['start_time']
    end_time    = db_record['end_time']
    file_size = db_record['file_size']
    state = db_record['state']
    log = db_record['log']
    element_storage_status = db_record['element_storage_status']
    
    # print ('....')
    
    #sqlcmd = "SELECT * FROM %s WHERE category_id = %s and filename = '%s' and path = '%s' and start_time = '%s' and end_time = '%s' and file_size = '%s' and state = '%s' and log = '%s' and element_storage_status = '%s'" %(table_name,category_id,filename,path,start_time,end_time,file_size,state,log,element_storage_status)
    # sqlcmd = "SELECT count(*) FROM %s WHERE category_id = %s and filename = '%s' and path = '%s' and start_time = '%s' and end_time = '%s' and file_size = '%s' and state = '%s' and log = '%s' and element_storage_status = '%s'" %(table_name,category_id,filename,path,start_time,end_time,file_size,state,log,element_storage_status)
    
    sqlcmd = "SELECT count(*) FROM %s WHERE category_id = %s and category_abbr_en = '%s' and filename = '%s' and path = '%s' and start_time = '%s' and end_time = '%s' and file_size = '%s' and state = '%s' and log = '%s' and element_storage_status = '%s'" %(table_name,category_id,category_abbr_en,filename,path,start_time,end_time,file_size,state,log,element_storage_status)
    ret_code = search_db(sqlcmd)
    # print (sqlcmd)
    
    record_time = get_current_BJT()##入库时间是本地时,即北京时

    # print (ret_code)
    # print (sqlcmd)
    # input()
    
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}

        update_condition_infos={
                    'category_id':category_id,
                    'category_abbr_en':category_abbr_en,                    
                    'filename':filename,
                    'path':path,
                    'start_time':start_time,
                    'end_time':end_time,
                    'file_size':file_size,
                    'state':state,
                    'log':log,
                    'element_storage_status':element_storage_status}    
        update_db(table_name,update_config_infos,update_condition_infos)
        
        
    elif 2==ret_code:
        insert_config_infos={
                    'category_id':category_id,
                    'category_abbr_en':category_abbr_en,
                    'filename':filename,
                    'path':path,
                    'record_time':record_time,
                    'start_time':start_time,
                    'end_time':end_time,
                    'file_size':file_size,
                    'state':state,
                    'log':log,
                    'element_storage_status':element_storage_status}       
        insert_db(table_name,insert_config_infos) 
    
    return
    
    
def record_product(db_record):
    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    """
    table_name = 'product_file_info'    
    
    category_abbr_en    = db_record['category_abbr_en']
    filename            = db_record['filename']
    path                = db_record['path']
    start_time          = db_record['start_time']
    end_time            = db_record['end_time']
    file_size           = db_record['file_size']
    log                 = db_record['log']
    
    
    #sqlcmd = "SELECT * FROM %s WHERE category_abbr_en = '%s' and filename = '%s' and path = '%s' and start_time = '%s' and end_time = '%s' and file_size = '%s' and log = '%s'" %(table_name,category_abbr_en,filename,path,start_time,end_time,file_size,log)    
    sqlcmd = "SELECT count(*) FROM %s WHERE category_abbr_en = '%s' and filename = '%s' and path = '%s' and start_time = '%s' and end_time = '%s' and file_size = '%s' and log = '%s'" %(table_name,category_abbr_en,filename,path,start_time,end_time,file_size,log)
    ret_code = search_db(sqlcmd)
    
    
    record_time = get_current_BJT()##入库时间是本地时,即北京时

    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}

        update_condition_infos={
                    'category_abbr_en':category_abbr_en,
                    'filename':filename,
                    'path':path,
                    'start_time':start_time,
                    'end_time':end_time,
                    'file_size':file_size,
                    'log':log}
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'category_abbr_en':category_abbr_en,
                    'filename':filename,
                    'path':path,
                    'record_time':record_time,
                    'start_time':start_time,
                    'end_time':end_time,
                    'file_size':file_size,
                    'log':log}       
        insert_db(table_name,insert_config_infos) 
    
    return
    
    
    
    
def record_alert(db_record):

    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    """
    
    table_name = 'alert_file_info'    
    
    event_type          = db_record['event_type']
    bj_time            = db_record['bj_time']
    event_level         = db_record['event_level']
    event_descrip       = db_record['event_descrip']
    sms                 = db_record['sms']
    log                 = db_record['log']
    
    #sqlcmd = "SELECT * FROM %s WHERE event_type = '%s' and utc_time = '%s' and event_level = '%s' and event_descrip = '%s' and sms = '%s' and log = '%s'" %(table_name,event_type,utc_time,event_level,event_descrip,sms,log)
    #sqlcmd = "SELECT count(*) FROM %s WHERE event_type = '%s' and utc_time = '%s' and event_level = '%s' and event_descrip = '%s' and sms = '%s' and log = '%s'" %(table_name,event_type,utc_time,event_level,event_descrip,sms,log)
    sqlcmd = "SELECT count(*) FROM %s WHERE event_type = '%s' and bj_time = '%s' and event_level = '%s' and event_descrip = '%s' and sms = '%s' and log = '%s'" %(table_name,event_type,bj_time,event_level,event_descrip,sms,log)
    ret_code = search_db(sqlcmd)
    
    
    record_time = get_current_BJT()##入库时间是本地时,即北京时

    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'event_type':event_type,
                    'bj_time':bj_time,
                    'event_level':event_level,
                    'event_descrip':event_descrip,
                    'sms':sms,
                    'log':log}    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'event_type':event_type,
                    'bj_time':bj_time,
                    'event_level':event_level,
                    'record_time':record_time,
                    'event_descrip':event_descrip,
                    'sms':sms,
                    'log':log}       
        insert_db(table_name,insert_config_infos) 
    
    return
    
    
def record_report(db_record):

    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    """
    
    table_name = 'report_file_info'    
    
    #record_time          = db_record['record_time']
    event_type           = db_record['event_type']
    utc_date_begin       = db_record['utc_date_begin']
    utc_date_end         = db_record['utc_date_end']
    event_level          = db_record['event_level']
    event_pmax           = db_record['event_pmax']
    path                 = db_record['path']    
    filename             = db_record['filename']    
    log                  = db_record['log']    
    
    #sqlcmd = "SELECT * FROM %s WHERE event_type = '%s' and utc_date_begin = '%s' and utc_date_end = '%s' and event_level = '%s' and event_pmax = '%s' and path = '%s' and filename = '%s' and log = '%s'" %(table_name,event_type,utc_date_begin,utc_date_end,event_level,event_pmax,path,filename,log)
    sqlcmd = "SELECT count(*) FROM %s WHERE event_type = '%s' and utc_date_begin = '%s' and utc_date_end = '%s' and event_level = '%s' and event_pmax = '%s' and path = '%s' and filename = '%s' and log = '%s'" %(table_name,event_type,utc_date_begin,utc_date_end,event_level,event_pmax,path,filename,log)
    ret_code = search_db(sqlcmd)
    
    
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'event_type':event_type,
                    'utc_date_begin':utc_date_begin,
                    'utc_date_end':utc_date_end,
                    'event_level':event_level,
                    'event_pmax':event_pmax,
                    'path':path,
                    'filename':filename,
                    'log':log}    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,        
                    'event_type':event_type,
                    'utc_date_begin':utc_date_begin,
                    'utc_date_end':utc_date_end,
                    'event_level':event_level,
                    'event_pmax':event_pmax,
                    'path':path,
                    'filename':filename,
                    'log':log}         
        insert_db(table_name,insert_config_infos) 
    
    return


def record_element_ace_ep(db_record):
    
    table_name = 'element_ace_ep'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    eles                                = db_record['eles']
    elediffflux_38to53                  = db_record['elediffflux_38to53']
    elediffflux_175to315                = db_record['elediffflux_175to315']
    pros                                = db_record['pros']
    prodiffflux_47to68                  = db_record['prodiffflux_47to68']    
    prodiffflux_115to195                = db_record['prodiffflux_115to195']    
    prodiffflux_310to580                = db_record['prodiffflux_310to580']    
    prodiffflux_795to1193               = db_record['prodiffflux_795to1193']    
    prodiffflux_1060to1900              = db_record['prodiffflux_1060to1900']    
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and eles = '%s' and elediffflux_38to53 = '%s' and elediffflux_175to315 = '%s' and pros = '%s' and prodiffflux_47to68 = '%s' and prodiffflux_115to195 = '%s' and prodiffflux_310to580 = '%s' and prodiffflux_795to1193 = '%s' and prodiffflux_1060to1900 = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,eles,elediffflux_38to53,elediffflux_175to315,pros,prodiffflux_47to68,prodiffflux_115to195,prodiffflux_310to580,prodiffflux_795to1193,prodiffflux_1060to1900,website,category_abbr_en)
    
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and eles = '%s' and elediffflux_38to53 = '%s' and elediffflux_175to315 = '%s' and pros = '%s' and prodiffflux_47to68 = '%s' and prodiffflux_115to195 = '%s' and prodiffflux_310to580 = '%s' and prodiffflux_795to1193 = '%s' and prodiffflux_1060to1900 = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,eles,elediffflux_38to53,elediffflux_175to315,pros,prodiffflux_47to68,prodiffflux_115to195,prodiffflux_310to580,prodiffflux_795to1193,prodiffflux_1060to1900,website,category_abbr_en)
    
    ret_code = search_db(sqlcmd)        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    # print (ret_code)
    # input()
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'eles':eles,
                    'elediffflux_38to53':elediffflux_38to53,
                    'elediffflux_175to315':elediffflux_175to315,
                    'pros':pros,
                    'prodiffflux_47to68':prodiffflux_47to68,
                    'prodiffflux_115to195':prodiffflux_115to195,
                    'prodiffflux_310to580':prodiffflux_310to580,
                    'prodiffflux_795to1193':prodiffflux_795to1193,
                    'prodiffflux_1060to1900':prodiffflux_1060to1900,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'eles':eles,
                    'elediffflux_38to53':elediffflux_38to53,
                    'elediffflux_175to315':elediffflux_175to315,
                    'pros':pros,
                    'prodiffflux_47to68':prodiffflux_47to68,
                    'prodiffflux_115to195':prodiffflux_115to195,
                    'prodiffflux_310to580':prodiffflux_310to580,
                    'prodiffflux_795to1193':prodiffflux_795to1193,
                    'prodiffflux_1060to1900':prodiffflux_1060to1900,
                    'website':website,
                    'category_abbr_en':category_abbr_en}       
        insert_db(table_name,insert_config_infos) 
        

def record_element_ace_mag(db_record):
    
    table_name = 'element_ace_mag'
    
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    s                                   = db_record['s']
    bx                                  = db_record['bx']
    by                                  = db_record['by']
    bz                                  = db_record['bz']
    bt                                  = db_record['bt']    
    lat                                 = db_record['lat']    
    lon                                 = db_record['lon']    
    bx_gse                              = db_record['bx_gse']    
    by_gse                              = db_record['by_gse']    
    bz_gse                              = db_record['bz_gse']    
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and s = '%s' and bx = '%s' and by = '%s' and bz = '%s' and bt = '%s' and lat = '%s' and lon = '%s' and bx_gse = '%s' and by_gse = '%s' and bz_gse = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,s,bx,by,bz,bt,lat,lon,bx_gse,by_gse,bz_gse,website,category_abbr_en)
    
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and s = '%s' and bx = '%s' and by = '%s' and bz = '%s' and bt = '%s' and lat = '%s' and lon = '%s' and bx_gse = '%s' and by_gse = '%s' and bz_gse = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,s,bx,by,bz,bt,lat,lon,bx_gse,by_gse,bz_gse,website,category_abbr_en)
    
    ret_code = search_db(sqlcmd)    
    record_time = get_current_BJT()##入库时间是本地时,即北京时

    # print (ret_code)
    # print (sqlcmd)
    # input()
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    's':s,
                    'bx':bx,
                    'by':by,
                    'bz':bz,
                    'bt':bt,
                    'lat':lat,
                    'lon':lon,
                    'bx_gse':bx_gse,
                    'by_gse':by_gse,
                    'bz_gse':bz_gse,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    
        # print (ret_code,record_time,utc_time)
        # input()
    
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    's':s,
                    'bx':bx,
                    'by':by,
                    'bz':bz,
                    'bt':bt,
                    'lat':lat,
                    'lon':lon,
                    'bx_gse':bx_gse,
                    'by_gse':by_gse,
                    'bz_gse':bz_gse,
                    'website':website,
                    'category_abbr_en':category_abbr_en}     
        insert_db(table_name,insert_config_infos) 

   
def record_element_ace_sis(db_record):
    
    table_name = 'element_ace_sis'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    proflux_gt10mev                     = db_record['proflux_gt10mev']
    proflux_gt30mev                     = db_record['proflux_gt30mev'] 
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and proflux_gt10mev = '%s' and proflux_gt30mev = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,proflux_gt10mev,proflux_gt30mev,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and proflux_gt10mev = '%s' and proflux_gt30mev = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,proflux_gt10mev,proflux_gt30mev,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'proflux_gt10mev':proflux_gt10mev,
                    'proflux_gt30mev':proflux_gt30mev,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,                    
                    'proflux_gt10mev':proflux_gt10mev,
                    'proflux_gt30mev':proflux_gt30mev,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 


def record_element_ace_sw(db_record):
    
    table_name = 'element_ace_sw'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    density                             = db_record['density']
    speed                               = db_record['speed']
    temp                                = db_record['temp']  
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and density = '%s' and speed = '%s' and temp = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,density,speed,temp,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and density = '%s' and speed = '%s' and temp = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,density,speed,temp,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'density':density,
                    'speed':speed,
                    'temp':temp,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'density':density,
                    'speed':speed,
                    'temp':temp,
                    'website':website,
                    'category_abbr_en':category_abbr_en}   
        insert_db(table_name,insert_config_infos) 

        
def record_element_ap(db_record):
    
    table_name = 'element_ap'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    ap                             = db_record['ap']
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and ap = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,ap,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and ap = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,ap,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'ap':ap,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'ap':ap,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 


def record_element_dst(db_record):
    
    table_name = 'element_dst'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    dst                                 = db_record['dst']
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and dst = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,dst,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and dst = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,dst,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'dst':dst,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'dst':dst,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 




def record_element_f107(db_record):
    
    table_name = 'element_f107'        
    #record_time          = db_record['record_time']
    utc_time                            = db_record['utc_time']
    carrington                          = db_record['carrington']
    obsflux                             = db_record['obsflux'] 
    adjflux                             = db_record['adjflux'] 
    ursiflux                            = db_record['ursiflux'] 
    website                             = db_record['website']    
    category_abbr_en                    = db_record['category_abbr_en']    
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and carrington = '%s' and obsflux = '%s' and adjflux = '%s' and ursiflux = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,carrington,obsflux,adjflux,ursiflux,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and carrington = '%s' and obsflux = '%s' and adjflux = '%s' and ursiflux = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,carrington,obsflux,adjflux,ursiflux,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'carrington':carrington,
                    'obsflux':obsflux,
                    'adjflux':adjflux,
                    'ursiflux':ursiflux,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'carrington':carrington,
                    'obsflux':obsflux,
                    'adjflux':adjflux,
                    'ursiflux':ursiflux,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 
        
        
def record_element_goes_ie(db_record):
    
    table_name = 'element_goes_ie'        
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                               = db_record['satellite']
    efgt0d8m                                = db_record['efgt0d8m'] 
    efgt2d0m                                = db_record['efgt2d0m'] 
    efgt4d0m                                = db_record['efgt4d0m'] 
    iefday                                  = db_record['iefday'] 
    level                                   = db_record['level'] 
    descrip                                 = db_record['descrip'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and efgt0d8m = '%s' and efgt2d0m = '%s' and efgt4d0m = '%s' and iefday = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,efgt0d8m,efgt2d0m,efgt4d0m,iefday,level,descrip,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and efgt0d8m = '%s' and efgt2d0m = '%s' and efgt4d0m = '%s' and iefday = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,efgt0d8m,efgt2d0m,efgt4d0m,iefday,level,descrip,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'efgt0d8m':efgt0d8m,
                    'efgt2d0m':efgt2d0m,
                    'efgt4d0m':efgt4d0m,
                    'iefday':iefday,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'efgt0d8m':efgt0d8m,
                    'efgt2d0m':efgt2d0m,
                    'efgt4d0m':efgt4d0m,
                    'iefday':iefday,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 

        
       
def record_element_goes_ip(db_record):
    
    table_name = 'element_goes_ip'        
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                               = db_record['satellite']
    pfgt01m                                 = db_record['pfgt01m'] 
    pfgt05m                                 = db_record['pfgt05m'] 
    pfgt10m                                 = db_record['pfgt10m'] 
    pfgt30m                                 = db_record['pfgt30m'] 
    pfgt50m                                 = db_record['pfgt50m'] 
    pfgt100m                                = db_record['pfgt100m'] 
    ad                                      = db_record['ad'] 
    an                                      = db_record['an'] 
    level                                   = db_record['level'] 
    descrip                                 = db_record['descrip']
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and pfgt01m = '%s' and pfgt05m = '%s' and pfgt10m = '%s' and pfgt30m = '%s'  and pfgt50m = '%s'  and pfgt100m = '%s'  and ad = '%s'  and an = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,pfgt01m,pfgt05m,pfgt10m,pfgt30m,pfgt50m,pfgt100m,ad,an,level,descrip,website,category_abbr_en)
    
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and pfgt01m = '%s' and pfgt05m = '%s' and pfgt10m = '%s' and pfgt30m = '%s'  and pfgt50m = '%s'  and pfgt100m = '%s'  and ad = '%s'  and an = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,pfgt01m,pfgt05m,pfgt10m,pfgt30m,pfgt50m,pfgt100m,ad,an,level,descrip,website,category_abbr_en)
    
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'pfgt01m':pfgt01m,
                    'pfgt05m':pfgt05m,
                    'pfgt10m':pfgt10m,
                    'pfgt30m':pfgt30m,
                    'pfgt50m':pfgt50m,
                    'pfgt100m':pfgt100m,
                    'ad':ad,
                    'an':an,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'pfgt01m':pfgt01m,
                    'pfgt05m':pfgt05m,
                    'pfgt10m':pfgt10m,
                    'pfgt30m':pfgt30m,
                    'pfgt50m':pfgt50m,
                    'pfgt100m':pfgt100m,
                    'ad':ad,
                    'an':an,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 


       
def record_element_goes_mag(db_record):
    
    table_name = 'element_goes_mag'        
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                               = db_record['satellite']
    hp                                      = db_record['hp'] 
    he                                      = db_record['he'] 
    hn                                      = db_record['hn'] 
    totalfield                              = db_record['totalfield']
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and hp = '%s' and he = '%s' and hn = '%s' and totalfield = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,hp,he,hn,totalfield,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and hp = '%s' and he = '%s' and hn = '%s' and totalfield = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,hp,he,hn,totalfield,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
    
    
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'hp':hp,
                    'he':he,
                    'hn':hn,
                    'totalfield':totalfield,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'hp':hp,
                    'he':he,
                    'hn':hn,
                    'totalfield':totalfield,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 
        
        
def record_element_goes_xr(db_record):
    
    table_name = 'element_goes_xr'        
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                               = db_record['satellite']
    time_resolution                                      = db_record['time_resolution'] 
    xr_short                                      = db_record['xr_short'] 
    xr_long                                      = db_record['xr_long'] 
    level                              = db_record['level']
    descrip                              = db_record['descrip']
    haf                              = db_record['haf']
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and time_resolution = '%s' and xr_short = '%s' and xr_long = '%s' and level = '%s' and descrip = '%s' and haf = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,time_resolution,xr_short,xr_long,level,descrip,haf,website,category_abbr_en)
    # ret_code = search_db(sqlcmd)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and time_resolution = '%s' and xr_short = '%s' and xr_long = '%s' and level = '%s' and descrip = '%s' and haf = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,time_resolution,xr_short,xr_long,level,descrip,haf,website,category_abbr_en)
    ret_code = search_db(sqlcmd)    
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'time_resolution':time_resolution,
                    'xr_short':xr_short,
                    'xr_long':xr_long,
                    'level':level,
                    'descrip':descrip,
                    'haf':haf,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'time_resolution':time_resolution,
                    'xr_short':xr_short,
                    'xr_long':xr_long,
                    'level':level,
                    'descrip':descrip,
                    'haf':haf,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 
        

def record_element_hpi(db_record):
    
    table_name = 'element_hpi'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    northhpi                                = db_record['northhpi']
    southhpi                                = db_record['southhpi'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and northhpi = '%s' and southhpi = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,northhpi,southhpi,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and northhpi = '%s' and southhpi = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,northhpi,southhpi,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'northhpi':northhpi,
                    'southhpi':southhpi,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'northhpi':northhpi,
                    'southhpi':southhpi,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
        insert_db(table_name,insert_config_infos) 


def record_element_kp(db_record):
    
    table_name = 'element_kp'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    kp                                      = db_record['kp']
    level                                   = db_record['level'] 
    descrip                                 = db_record['descrip'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and kp = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,kp,level,descrip,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and kp = '%s' and level = '%s' and descrip = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,kp,level,descrip,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'kp':kp,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'kp':kp,
                    'level':level,
                    'descrip':descrip,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
        
      
def record_element_rad(db_record):
    
    table_name = 'element_rad'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    station                                 = db_record['station']
    freq                                    = db_record['freq'] 
    flux                                    = db_record['flux'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and station = '%s' and freq = '%s' and flux = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,station,freq,flux,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and station = '%s' and freq = '%s' and flux = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,station,freq,flux,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'station':station,
                    'freq':freq,
                    'flux':flux,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'station':station,
                    'freq':freq,
                    'flux':flux,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
      
      
def record_element_ssn(db_record):
    
    table_name = 'element_ssn'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    sn                                      = db_record['sn']
    std                                     = db_record['std'] 
    num_obs                                 = db_record['num_obs'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    #sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and sn = '%s' and std = '%s' and num_obs = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,sn,std,num_obs,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and sn = '%s' and std = '%s' and num_obs = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,sn,std,num_obs,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'sn':sn,
                    'std':std,
                    'num_obs':num_obs,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'sn':sn,
                    'std':std,
                    'num_obs':num_obs,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
        
        
def record_element_ste_het(db_record):
    
    table_name = 'element_ste_het'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                                      = db_record['satellite']
    proflux_13to21mev                                     = db_record['proflux_13to21mev'] 
    proflux_40to100mev                                 = db_record['proflux_40to100mev'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and proflux_13to21mev = '%s' and proflux_40to100mev = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,proflux_13to21mev,proflux_40to100mev,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and proflux_13to21mev = '%s' and proflux_40to100mev = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,proflux_13to21mev,proflux_40to100mev,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'proflux_13to21mev':proflux_13to21mev,
                    'proflux_40to100mev':proflux_40to100mev,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'proflux_13to21mev':proflux_13to21mev,
                    'proflux_40to100mev':proflux_40to100mev,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
        
      
def record_element_ste_mag(db_record):
    
    table_name = 'element_ste_mag'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                                      = db_record['satellite']
    br                                     = db_record['br'] 
    bt                                 = db_record['bt'] 
    bn                                 = db_record['bn'] 
    btotal                                 = db_record['btotal'] 
    lat                                 = db_record['lat'] 
    lon                                 = db_record['lon'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and br = '%s' and bt = '%s' and bn = '%s' and btotal = '%s' and lat = '%s' and lon = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,br,bt,bn,btotal,lat,lon,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and br = '%s' and bt = '%s' and bn = '%s' and btotal = '%s' and lat = '%s' and lon = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,br,bt,bn,btotal,lat,lon,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'br':br,
                    'bt':bt,
                    'bn':bn,
                    'btotal':btotal,
                    'lat':lat,
                    'lon':lon,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'br':br,
                    'bt':bt,
                    'bn':bn,
                    'btotal':btotal,
                    'lat':lat,
                    'lon':lon,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
        
 
def record_element_ste_sw(db_record):
    
    table_name = 'element_ste_sw'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    satellite                               = db_record['satellite']
    density                                 = db_record['density'] 
    speed                                   = db_record['speed'] 
    temp                                    = db_record['temp'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and satellite = '%s' and density = '%s' and speed = '%s' and temp = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,density,speed,temp,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and satellite = '%s' and density = '%s' and speed = '%s' and temp = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,satellite,density,speed,temp,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'density':density,
                    'speed':speed,
                    'temp':temp,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'satellite':satellite,
                    'density':density,
                    'speed':speed,
                    'temp':temp,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 

        
def record_element_swpc_flare(db_record):
    
    table_name = 'element_swpc_flare'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    f107                                      = db_record['f107']
    sunspotnum                                     = db_record['sunspotnum'] 
    sunspotarea                                 = db_record['sunspotarea'] 
    newregions                                 = db_record['newregions'] 
    xraybkgdflux                                 = db_record['xraybkgdflux'] 
    flaresxrayc                                 = db_record['flaresxrayc'] 
    flaresxraym                                 = db_record['flaresxraym'] 
    flaresxrayx                                 = db_record['flaresxrayx'] 
    flaresopticals                                 = db_record['flaresopticals'] 
    flaresoptical1                                 = db_record['flaresoptical1'] 
    flaresoptical2                                 = db_record['flaresoptical2'] 
    flaresoptical3                                 = db_record['flaresoptical3'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and f107 = '%s' and sunspotnum = '%s' and sunspotarea = '%s' and newregions = '%s' and xraybkgdflux = '%s' and flaresxrayc = '%s' and flaresxraym = '%s' and flaresxrayx = '%s' and flaresopticals = '%s'  and flaresoptical1 = '%s'  and flaresoptical2 = '%s'  and flaresoptical3 = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,f107,sunspotnum,sunspotarea,newregions,xraybkgdflux,flaresxrayc,flaresxraym,flaresxrayx,flaresopticals,flaresoptical1,flaresoptical2,flaresoptical3,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and f107 = '%s' and sunspotnum = '%s' and sunspotarea = '%s' and newregions = '%s' and xraybkgdflux = '%s' and flaresxrayc = '%s' and flaresxraym = '%s' and flaresxrayx = '%s' and flaresopticals = '%s'  and flaresoptical1 = '%s'  and flaresoptical2 = '%s'  and flaresoptical3 = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,f107,sunspotnum,sunspotarea,newregions,xraybkgdflux,flaresxrayc,flaresxraym,flaresxrayx,flaresopticals,flaresoptical1,flaresoptical2,flaresoptical3,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'f107':f107,
                    'sunspotnum':sunspotnum,
                    'sunspotarea':sunspotarea,
                    'newregions':newregions,
                    'xraybkgdflux':xraybkgdflux,
                    'flaresxrayc':flaresxrayc,
                    'flaresxraym':flaresxraym,
                    'flaresxrayx':flaresxrayx,
                    'flaresopticals':flaresopticals,
                    'flaresoptical1':flaresoptical1,
                    'flaresoptical2':flaresoptical2,
                    'flaresoptical3':flaresoptical3,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'f107':f107,
                    'sunspotnum':sunspotnum,
                    'sunspotarea':sunspotarea,
                    'newregions':newregions,
                    'xraybkgdflux':xraybkgdflux,
                    'flaresxrayc':flaresxrayc,
                    'flaresxraym':flaresxraym,
                    'flaresxrayx':flaresxrayx,
                    'flaresopticals':flaresopticals,
                    'flaresoptical1':flaresoptical1,
                    'flaresoptical2':flaresoptical2,
                    'flaresoptical3':flaresoptical3,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 


def record_element_tec(db_record):
    
    table_name = 'element_tec'
    #record_time          = db_record['record_time']
    utc_time                                = db_record['utc_time']
    site                                      = db_record['site']
    tec                                     = db_record['tec'] 
    fof2                                 = db_record['fof2'] 
    fof1                                 = db_record['fof1'] 
    m                                 = db_record['m'] 
    muf                                 = db_record['muf'] 
    fmin                                 = db_record['fmin'] 
    website                                 = db_record['website']    
    category_abbr_en                        = db_record['category_abbr_en']
    
    # sqlcmd = "SELECT * FROM %s WHERE utc_time = '%s' and site = '%s' and tec = '%s' and fof2 = '%s' and fof1 = '%s' and m = '%s' and muf = '%s' and fmin = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,site,tec,fof2,fof1,m,muf,fmin,website,category_abbr_en)
    sqlcmd = "SELECT count(*) FROM %s WHERE utc_time = '%s' and site = '%s' and tec = '%s' and fof2 = '%s' and fof1 = '%s' and m = '%s' and muf = '%s' and fmin = '%s' and website = '%s' and category_abbr_en = '%s'" %(table_name,utc_time,site,tec,fof2,fof1,m,muf,fmin,website,category_abbr_en)
    ret_code = search_db(sqlcmd)
        
    record_time = get_current_BJT()##入库时间是本地时,即北京时
    
    ##如果有,直接更新
    if 1==ret_code:
        update_config_infos={
                    'record_time':record_time}
        
        update_condition_infos={
                    'utc_time':utc_time,
                    'site':site,
                    'tec':tec,
                    'fof2':fof2,
                    'fof1':fof1,
                    'm':m,
                    'muf':muf,
                    'fmin':fmin,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        update_db(table_name,update_config_infos,update_condition_infos)
        
    elif 2==ret_code:
        insert_config_infos={
                    'record_time':record_time,
                    'utc_time':utc_time,
                    'site':site,
                    'tec':tec,
                    'fof2':fof2,
                    'fof1':fof1,
                    'm':m,
                    'muf':muf,
                    'fmin':fmin,
                    'website':website,
                    'category_abbr_en':category_abbr_en}
                    
        insert_db(table_name,insert_config_infos) 
        
        
def record_element(element_extract_json_file,db_record):

    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    2. 目前没有
    """
    
    if 'element_ace_ep' in element_extract_json_file:
        record_element_ace_ep(db_record)
    if 'element_ace_mag' in element_extract_json_file:
        record_element_ace_mag(db_record)
    if 'element_ace_sis' in element_extract_json_file:
        record_element_ace_sis(db_record)
    if 'element_ace_sw' in element_extract_json_file:
        record_element_ace_sw(db_record)
    if 'element_ap' in element_extract_json_file:
        record_element_ap(db_record)
    if 'element_dst' in element_extract_json_file:
        record_element_dst(db_record)
    if 'element_f107' in element_extract_json_file:
        record_element_f107(db_record)
    if 'element_goes_ie' in element_extract_json_file:
        record_element_goes_ie(db_record)
    if 'element_goes_ip' in element_extract_json_file:
        record_element_goes_ip(db_record)
    if 'element_goes_mag' in element_extract_json_file:
        record_element_goes_mag(db_record)
    if 'element_goes_xr' in element_extract_json_file:
        record_element_goes_xr(db_record)
    if 'element_hpi' in element_extract_json_file:
        record_element_hpi(db_record)
    if 'element_kp' in element_extract_json_file:
        record_element_kp(db_record)
    if 'element_rad' in element_extract_json_file:
        record_element_rad(db_record)
    if 'element_ssn' in element_extract_json_file:
        record_element_ssn(db_record)
    if 'element_ste_het' in element_extract_json_file:
        record_element_ste_het(db_record)
    if 'element_ste_mag' in element_extract_json_file:
        record_element_ste_mag(db_record)
    if 'element_ste_sw' in element_extract_json_file:
        record_element_ste_sw(db_record)        
    if 'element_swpc_flare' in element_extract_json_file:
        record_element_swpc_flare(db_record)    
    if 'element_tec' in element_extract_json_file:
        record_element_tec(db_record)
        
    return
    
    
    
    
def delete_create_event_configuration(): 
    
    pgt=PostgresTable()
    db_name = configs['db_name']       
    table_name = 'event_configuration'      
    
    ####删除表
    pgt.delete_table(db_name,table_name)
    print ('delete_table event_configuration finish')
    
    
    ####创建表 
    pgt.create_event_configuration_table(db_name)
    print ('create_event_configuration_table finish.')    
    
    
    
def record_event_configuration(db_record):

    """
    1. record_time入库时间不作为查询条件,导入数据然后入库的实际时间作为record_time
    """
    
    table_name          = 'event_configuration'
    
    category            = db_record['category']
    level               = db_record['level']
    descrip             = db_record['descrip']
    measure             = db_record['measure']
    level_number        = db_record['level_number']
    
    
    ####插入记录      
    insert_config_infos={
                'category':category,
                'level':level,
                'descrip':descrip,
                'measure':measure,
                'level_number':level_number}         
    insert_db(table_name,insert_config_infos) 
    
    return

    
def extract_zip(zip_filename,des_path='/'):
    """
    1. 提取之后的路径，需要传递根路径/
    2. 提取路径 缺少/，home/YJY015/data/iono/IGGCAS/TEC/TECMAPHOUR/202006/20200611/TECMAPHOUR_20200611_000000.jpg
    3. des_path，如果在内网机，需要共享磁盘，share_disk_rootpath
    """
    
    data_file_info_json       =   ''
    product_file_info_json    =   ''
    alert_file_info_json      =   ''
    report_file_info_json     =   ''
    element_extract_json      =   []
    event_configuration_json  =   ''    
    
    z = zipfile.ZipFile(zip_filename, 'r') # 这里的第二个参数用r表示是读取zip文件，w是创建一个zip文件
    for p in z.namelist():

        ##des_path参数，解压之后的根目录，若没有传参，默认是当前路径
        z.extract(p, des_path)
        #z.extract(p)
        
        ####extract解压的data,product,report,默认解压到/home/YJY015目录下
        
        ####json文件需要提取
        ##提取路径缺少斜杠/,需要补全路径
        if 'data_file_info.json' in p:
            data_file_info_json = des_path + p
        if 'product_file_info.json' in p:
            product_file_info_json = des_path + p
        if 'alert_file_info.json' in p:
            alert_file_info_json = des_path + p            
        if 'report_file_info.json' in p:
            report_file_info_json = des_path + p   
        if 'element_ace_ep.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ace_mag.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ace_sis.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ace_sw.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ap.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_dst.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_f107.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_goes_ie.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_goes_ip.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_goes_mag.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_goes_xr.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_hpi.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_kp.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_rad.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ssn.json' in p:
            element_extract_json.append( des_path + p)            
        if 'element_ste_het.json' in p:
            element_extract_json.append( des_path + p)   
        if 'element_ste_mag.json' in p:
            element_extract_json.append( des_path + p)
        if 'element_ste_sw.json' in p:
            element_extract_json.append( des_path + p)             
        if 'element_swpc_flare.json' in p:
            element_extract_json.append( des_path + p)  
        if 'element_tec.json' in p:
            element_extract_json.append( des_path + p)              
        if 'event_configuration.json' in p:
            event_configuration_json = des_path + p   
            
            
    ##解压之后,关闭文件
    z.close()
    
    # print(data_file_info_json)
    # input()
    
    return data_file_info_json,product_file_info_json,alert_file_info_json,report_file_info_json,element_extract_json,event_configuration_json
    
    
    
    
def import_data(input_fullpath):
    """
    1. 输入zip文件全路径
    /home/YJY015/data_test/2020-06-11.zip
    
    """
    
    
    log_starttime  = get_current_BJT()
    
    ####实例化日志类
    loggings=Loggings(log_starttime,'import')
    loggings.debug_log(input_fullpath)
    
    input_rootpath                  = configs['rootpath']
    share_disk_rootpath             = configs['share_disk_rootpath']
    share_disk_open                 = configs['share_disk_open']
    
    
    ##数据导入前,先判断导入服务器的根路径是否存在
    if not os.path.exists(input_rootpath):
        os.makedirs(input_rootpath)
        
    ##提取zip文件,并提取到目录结构对应的路径下，并返回提取的json文件，作为入库使用
    try:
        ####解压路径,需要拼接共享磁盘根路径
        ####兼容外网,内网路径
        if 'True' == share_disk_open:
            des_path = share_disk_rootpath
        if 'False' == share_disk_open:
            des_path = '/'        

        data_file_info_json,product_file_info_json,alert_file_info_json,report_file_info_json,element_extract_json,event_configuration_json = extract_zip(input_fullpath,des_path)
    except Exception as e:
        ##如果异常,UI界面如何获取异常
        loggings.debug_log(traceback.format_exc())        
        raise Exception(traceback.format_exc())
    #loggings.debug_log(data_file_info_json)
    
    ##数据入库,入库判断,除了id,record_time不同,其它参数都是入库的判别条件
    ##根据zip文件种json文件,拷贝文件到本地路径
    
    ####1.先读data.json文件
    # print (data_file_info_json)
    # print (type(data_file_info_json))
    # input()
    
    if not os.path.exists(data_file_info_json):
        # print ('do not ')
        # input()        
        loggings.debug_log('data_file_info_json文件不存在,没有导出data_file_info信息,data_file_info_json = %s'%data_file_info_json) #输出hadoop异常操作到log日志里
    else:
        try:
            fh = open(data_file_info_json,'r',encoding='utf-8')
        except Exception as e:
            ##如果异常,UI界面如何获取异常
            loggings.debug_log(traceback.format_exc())        
            raise Exception(traceback.format_exc())
        
        content = fh.read()                         #使用loads()方法需要先读文件
        fh.close()
        # print (content)
        # input()
        try:
            db_records = json.loads(content)           #loads()返回结果为list
            #print (db_records)
        except Exception as e:
            ##如果异常,UI界面如何获取异常
            loggings.debug_log(traceback.format_exc())        
            raise Exception(traceback.format_exc())
            
        # print (type(db_records))
        # input()
        
        for db_reocord in db_records:
            record_data(db_reocord)
            
        # try:
            # map_res = map(record_data,db_records)
            # # print (map_res)
            # # print (list(map_res))
            # # input()            
        # except Exception as e:
            # ##如果异常,UI界面如何获取异常
            # loggings.debug_log(traceback.format_exc())        
            # raise Exception(traceback.format_exc())
            
        print ('record_data finish.')
        loggings.debug_log('record_data finish.')   #输出hadoop异常操作到log日志里
        
    
    ####2.读product.json文件
    if not os.path.exists(product_file_info_json):
        loggings.debug_log('product_file_info_json文件不存在,没有导出product_file_info信息,product_file_info_json = %s'%product_file_info_json) #输出hadoop异常操作到log日志里
    else:    
        fh = open(product_file_info_json,'r',encoding='utf-8')
        content = fh.read()                         #使用loads()方法需要先读文件
        fh.close()
        db_records = json.loads(content)           #loads()返回结果为list
        
        for db_reocord in db_records:
            record_product(db_reocord)
        # map(record_product,db_records)  
        
        print ('record_product finish.')
        loggings.debug_log('record_product finish.')#输出hadoop异常操作到log日志里
    

    ####3.读alert.json文件
    if not os.path.exists(alert_file_info_json):
        loggings.debug_log('alert_file_info_json文件不存在,没有导出alert_file_info信息,alert_file_info_json = %s'%alert_file_info_json) #输出hadoop异常操作到log日志里
    else:     
        #print (alert_file_info_json)
        fh = open(alert_file_info_json,'r',encoding='utf-8')
        content = fh.read()                         #使用loads()方法需要先读文件
        fh.close()
        db_records = json.loads(content)           #loads()返回结果为list       
        
        for db_reocord in db_records:
            record_alert(db_reocord)
        #map(record_alert,db_records)              
        
        print ('record_alert finish.')
        loggings.debug_log('record_alert finish.')  #输出hadoop异常操作到log日志里
    
    
    ####4.读report.json文件
    if not os.path.exists(report_file_info_json):
        loggings.debug_log('report_file_info_json文件不存在,没有导出report_file_info信息,report_file_info_json = %s'%report_file_info_json)  #输出hadoop异常操作到log日志里
    else:     
        #print (alert_file_info_json)
        fh = open(report_file_info_json,'r',encoding='utf-8')
        content = fh.read()                         #使用loads()方法需要先读文件
        fh.close()
        db_records = json.loads(content)           #loads()返回结果为list
        
        for db_reocord in db_records:
            record_report(db_reocord)
        #map(record_report,db_records)             
        
        print ('record_report finish.')
        loggings.debug_log('record_report finish.')     #输出hadoop异常操作到log日志里
    
    
    ####5.读element文件
    for element_extract_json_file in element_extract_json:
        if not os.path.exists(element_extract_json_file):
            loggings.debug_log('%s文件不存在,没有导出%s信息,element_extract_json_file = %s'%element_extract_json_file) #输出hadoop异常操作到log日志里
        else:     
            #print (alert_file_info_json)
            fh = open(element_extract_json_file,'r',encoding='utf-8')
            content = fh.read()                         #使用loads()方法需要先读文件
            fh.close()
            db_records = json.loads(content)           #loads()返回结果为list
            
            for db_reocord in db_records:
                record_element(element_extract_json_file,db_reocord)
                
            # if 'element_ace_ep' in element_extract_json_file:
                # #record_element_ace_ep(db_record)
                # map(record_element_ace_ep,db_records)
            # if 'element_ace_mag' in element_extract_json_file:
                # #record_element_ace_mag(db_record)
                # map(record_element_ace_mag,db_records)                
            # if 'element_ace_sis' in element_extract_json_file:
                # #record_element_ace_sis(db_record)
                # map(record_element_ace_sis,db_records)                 
            # if 'element_ace_sw' in element_extract_json_file:
                # #record_element_ace_sw(db_record)
                # map(record_element_ace_sw,db_records)                 
            # if 'element_ap' in element_extract_json_file:
                # #record_element_ap(db_record)
                # map(record_element_ap,db_records)                 
            # if 'element_dst' in element_extract_json_file:
                # #record_element_dst(db_record)
                # map(record_element_dst,db_records)                 
            # if 'element_f107' in element_extract_json_file:
                # #record_element_f107(db_record)
                # map(record_element_f107,db_records)                 
            # if 'element_goes_ie' in element_extract_json_file:
                # #record_element_goes_ie(db_record)
                # map(record_element_goes_ie,db_records)                 
            # if 'element_goes_ip' in element_extract_json_file:
                # #record_element_goes_ip(db_record)
                # map(record_element_goes_ip,db_records)                 
            # if 'element_goes_mag' in element_extract_json_file:
                # #record_element_goes_mag(db_record)
                # map(record_element_goes_mag,db_records)                 
            # if 'element_goes_xr' in element_extract_json_file:
                # #record_element_goes_xr(db_record)
                # map(record_element_goes_xr,db_records)                 
            # if 'element_hpi' in element_extract_json_file:
                # #record_element_hpi(db_record)
                # map(record_element_hpi,db_records)                 
            # if 'element_kp' in element_extract_json_file:
                # #record_element_kp(db_record)
                # map(record_element_kp,db_records)                 
            # if 'element_rad' in element_extract_json_file:
                # #record_element_rad(db_record)
                # map(record_element_rad,db_records)                 
            # if 'element_ssn' in element_extract_json_file:
                # #record_element_ssn(db_record)
                # map(record_element_ssn,db_records)                 
            # if 'element_ste_het' in element_extract_json_file:
                # #record_element_ste_het(db_record)
                # map(record_element_ste_het,db_records) 
            # if 'element_ste_mag' in element_extract_json_file:
                # #record_element_ste_mag(db_record)
                # map(record_element_ste_mag,db_records)                 
            # if 'element_ste_sw' in element_extract_json_file:
                # #record_element_ste_sw(db_record)        
                # map(record_element_ste_sw,db_records)                 
            # if 'element_swpc_flare' in element_extract_json_file:
                # #record_element_swpc_flare(db_record)   
                # map(record_element_swpc_flare,db_records)                 
            # if 'element_tec' in element_extract_json_file:
                # #record_element_tec(db_record)  
                # map(record_element_tec,db_records)
                
                
            print ('%s finish.'%element_extract_json_file)
            loggings.debug_log('%s finish.'%element_extract_json_file)  #输出hadoop异常操作到log日志里
            
            
    ####5.读event_configuration.json文件
    if not os.path.exists(event_configuration_json):
        loggings.debug_log('event_configuration_json文件不存在,没有导出event_configuration信息,event_configuration_json = %s'%event_configuration_json)  #输出hadoop异常操作到log日志里
    else:     
        #print (alert_file_info_json)
        fh = open(event_configuration_json,'r',encoding='utf-8')
        content = fh.read()                         #使用loads()方法需要先读文件
        fh.close()
        db_records = json.loads(content)           #loads()返回结果为list
                
        ##先删除,再创建表
        delete_create_event_configuration()
        
        ##插入新的记录        
        for db_reocord in db_records:
            record_event_configuration(db_reocord)
        #map(record_event_configuration,db_records)              
        
        print ('%s finish.'%event_configuration_json)
        loggings.debug_log('%s finish.'%event_configuration_json)  #输出hadoop异常操作到log日志里     
        
    return 0
    
    
def clean_up_import_dir():
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    
    
    ####内网机需要配置共享磁盘根路径
    filepath = configs['import_rootpath']    
    # share_disk_rootpath = configs['share_disk_rootpath']
    # share_disk_open = configs['share_disk_open']
    
    # if 'True' == share_disk_open:
        # filepath = share_disk_rootpath + filepath
    # if 'False' == share_disk_open:
        # filepath = filepath    
    
    ####判断有无路径,没有需要创建,否则listdir报错
    if not os.path.exists(filepath):
        os.makedirs(filepath)    
    
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            
    
    
if __name__ == "__main__":
    if (len(sys.argv) == 2):
        argv0 = sys.argv[0]
        argv1 = sys.argv[1]##导入压缩包zip文件,全路径
        
        print ('argv0 = %s'%argv0)
        print ('argv1 = %s'%argv1)
        
        ####提取argv1参数里zip文件日期
        filepath,filename = os.path.split(argv1)
        filesize = os.path.getsize(argv1)
        filesize_MB = int(filesize/1024/1024)
        
        yyyymmdd = filename[0:filename.rfind(".")]        
        startime    =   yyyymmdd
        endtime     =   yyyymmdd
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
        
        ####数据导出,监控状态初始化
        start_time=search_starttime
        end_time=search_endtime
        ret_code=check_db(start_time,end_time)
        
        
        if 0==ret_code:
            print ('之前有过此时间段的导入操作,但是status=3，成功，不需要再进行导入操作,需要继续导入,可以继续导入')
            ####更改数据导出的监控状态
            update_time  = get_current_BJT()
            config_infos={
                        'update_time':update_time,
                        'status':'4',
                        'filesize':filesize_MB}#配置更新之后的值，4是更新中
            # condition_infos={             
                        # 'start_time':start_time,
                        # 'end_time':end_time,
                        # 'status':'False'}
            condition_infos={             
                        'start_time':start_time,
                        'end_time':end_time}
            table_name  = 'import_monitor'                             
            update_db(table_name,config_infos,condition_infos)
            
            #return ##之前有过此时间段的删除操作,不需要再进行删除操作
        if 1==ret_code:
            print ('之前有过此时间段的导入操作,但是status状态为: 1(失败)，2(导入中),需要再进行一次导入操作')
            ####更改数据导出的监控状态
            update_time  = get_current_BJT()
            config_infos={
                        'update_time':update_time,
                        'status':'4'}#配置更新之后的值，4是更新中
            # condition_infos={             
                        # 'start_time':start_time,
                        # 'end_time':end_time,
                        # 'status':'False'}
            condition_infos={             
                        'start_time':start_time,
                        'end_time':end_time}
            table_name  = 'import_monitor'                             
            update_db(table_name,config_infos,condition_infos)
            
            #pass ##之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作
        if 2==ret_code:
            print ('之前没有此时间段的导入操作,需要插入初始状态记录')
            record_time  = get_current_BJT() 
            update_time  = get_current_BJT()  
            status='2'                      ##2导入中            
            record_db(record_time,update_time,start_time,end_time,status,filesize_MB) ##之前没有此时间段的删除操作,需要插入初始状态记录
        
        
        try:
            import_data(argv1)
            
            ####更改数据导出的监控状态
            update_time  = get_current_BJT()
            config_infos={
                        'update_time':update_time,
                        'status':'3',
                        'filesize':filesize_MB}#配置更新之后的值，3是成功
            # condition_infos={             
                        # 'start_time':start_time,
                        # 'end_time':end_time,
                        # 'status':'False'}
            condition_infos={             
                        'start_time':start_time,
                        'end_time':end_time}
            table_name  = 'import_monitor'                             
            update_db(table_name,config_infos,condition_infos)
            
        except Exception as e:
            ##如果异常,UI界面如何获取异常
            
            ####如果异常，更改数据导出的监控状态
            update_time  = get_current_BJT()
            config_infos={
                        'update_time':update_time,
                        'status':'1',
                        'filesize':filesize_MB}#配置更新之后的值，1是失败
            # condition_infos={             
                        # 'start_time':start_time,
                        # 'end_time':end_time,
                        # 'status':'False'}
            condition_infos={             
                        'start_time':start_time,
                        'end_time':end_time}
            table_name  = 'import_monitor'                             
            update_db(table_name,config_infos,condition_infos)  
            
            raise Exception(traceback.format_exc())   
            

        ##每次进入import功能,执行一次/home/YJY015/import/目录清除,是在导入数据之后,进行清理,如果导入之前清理导致文件不存在
        clean_up_import_dir()
        #input()
            
            
            
            
            
            