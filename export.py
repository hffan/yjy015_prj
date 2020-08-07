#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
@user guide
2020-05-27 16:41:07
                    1. 测试数据导出功能 开始时间，结束时间到天，cd /home/YJY015/code;  python3 export.py 2020-07-10 2020-07-10 /home/YJY015/test/2020-07-10.zip
                    2. 测试gif动图功能，输入时间是UTC时间，不是北京时间  
                       cd /home/YJY015/code; python3 export.py SDO_AIA_0094 '2020-05-27 04:00:00' '2020-05-27 08:00:00' 4 .gif /home/YJY015/test/test.gif
                       数据库里查询的图片，默认按时间前后顺序排列，不需要重新排序
                       gif图传入fps为字符串也可以运行
                    3. 测试avi功能，输入时间是UTC时间，不是北京时间  
                       cd /home/YJY015/code; python3 export.py SDO_AIA_0094 '2020-05-27 04:00:00' '2020-05-27 08:00:00' 0.5 .avi /home/YJY015/test/test.avi
                    
                    
@modify history
2020-05-27 14:47:16
                    1. 根据后缀名和开始时间，结束时间，导致gif，avi，dat文件
                    2. 根据argv的个数和组合判断是哪一个功能
                    
2020-07-14 10:02:44
                    1. 导出,需要先清理; 可以不用覆盖,因为导出前已经做了清空处理
                       因为调用python export.py脚本,然后java需要先导出到/home/YJY015/export目录,,如果export.py后清理将导致文件不存在
                    2. 导出要素提取表,如果要导出的时间段不存在,则json文件也不存在
2020-07-15 11:33:12
                    1. 导出zip的名称,按天导出,zip日志只有1天;导入的时候,从zip名称上截取日期作为start_time,end_time的日期
                    2. 导出json文件统一放到/home/YJY015/json/export文件夹下,json文件夹下比如导出2020-07-06的数据,json全路径为/home/YJY015/json/export/2020-07-06/*.json文件
                    3. 导出完,需要把/home/YJY015/json/2020-07-06/清空,如果不清空,07-06这1天中午导出的,到了晚上07-06的记录又增加了,后期再导出可能记录不一样
                       可能文件个数或者data或者product被删除了,导致没有,导出压缩的时候,把之前的json文件也导入进去,导致导入功能会导入多余的数据;也可以不删除,作为一个导出文件的记录
                       后期排查问题,可以查看
                    4. 导入功能的json文件夹,不需要清理,比如内网机/home/YJY015/json/import/2020-07-06/
                    5. export_monitor表,status状态,如果更新,不论是true，false，都需要更新，updatetime更新为入库的时间
                    
2020-07-23 15:53:23 
                    1. 增加export路径listdir之前,os.path.exists()判断,没有就创建
                    
2020-08-06 18:45:10
                    1. export_monitor增加filesize，float8,文件大小，单位MB
                    
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


import interact_opt.make_gif
import interact_opt.make_video
import interact_opt.zipCompressLst

import json


def record_db(record_time,update_time,start_time,end_time,status,filesize):
    db_name = configs['db_name']
    table_name  = 'export_monitor'    
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


def update_db(config_infos,condition_infos):
    db_name     = configs['db_name']
    table_name  = 'export_monitor'    
    pga         =PostgresArchive()  
    pga.update_db_table(db_name,table_name,config_infos,condition_infos) 
    return
    
        
def check_db(start_time,end_time):
    """
    1. 首先,查询数据库,查看是否之前删除过数据,有删除记录
    2. 如果status=True说明之前删除成功,这次删除就是多余操作,直接return结束程序
    3. 如果status=False说明之前的程序没有删除,或者删除中途出错,或者删除之后,没有入库导致status为False,这种情况,需要再运行一次删除,并更改status的状态
    4. 如果status查询失败,说明之前没有进行删除操作,这次需要重新录入初始化status状态,删除数据,更改status状态为True
    5. 如果数据库中不存在data,product产品数据,也需要update,status的状态为True,也认为此次操作顺利完成,否则前端读status状态为false,认为删除操作一直进行
    """
    db_name     =   configs['db_name']
    table_name  =   'export_monitor'
    pga         =   PostgresArchive() 
     
    sqlcmd="SELECT * FROM %s WHERE start_time = '%s' and end_time = '%s'"%(table_name,start_time,end_time)
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
        
        
def export_gif(category_abbr_en,starttime,endtime,frame_ps,output_fullpath):

    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_gif')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']      
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'data_file_info'
    

    search_starttime='\'%s\''%starttime
    search_endtime  ='\'%s\''%endtime
    category_abbr_en='\'%s\''%(category_abbr_en)   
    #sqlcmd='SELECT data_file_info.path,data_file_info.filename FROM data_file_info INNER JOIN data_category ON data_file_info.category_id = data_category.category_id WHERE data_category.category_abbr_en = %s and start_time BETWEEN %s and %s'%(category_abbr_en,search_starttime,search_endtime)
    sqlcmd='SELECT data_file_info.path,data_file_info.filename FROM data_file_info WHERE data_file_info.category_abbr_en = %s and start_time BETWEEN %s and %s'%(category_abbr_en,search_starttime,search_endtime)
               
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        infos = traceback.format_exc()
        loggings.debug_log(infos)#输出log日志里       
        raise Exception(traceback.format_exc())  
    
    
    file_list=[]
    if(searchinfos):
        for searchinfo in searchinfos:
            path = searchinfo['path']
            filename = searchinfo['filename']                
            input_fullfilename = input_rootpath + '/' + path + '/' + filename
            
            ####图片在本地不存在,或者图片大小非性,如果图片大小为0,剔除掉
            if not os.path.exists(input_fullfilename) or os.path.getsize(input_fullfilename) == 0:
                continue
            file_list.append(input_fullfilename)
            
    else:
        infos = '数据库 %s,产品 %s不存在,时间段%s %s'%(table_name,category_abbr_en,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return 
        #raise Exception(infos)
        #print ('数据库中不存在，%s' % category_abbr_en)
    
  
    ####压缩
    try:
        interact_opt.make_gif.img2gif(output_fullpath,file_list,fps=frame_ps)                 
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    return
    
    
def export_avi(category_abbr_en,starttime,endtime,frame_ps,output_fullpath):

    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_avi')
    
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']         
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'data_file_info'
    

    search_starttime='\'%s\''%starttime
    search_endtime  ='\'%s\''%endtime
    category_abbr_en='\'%s\''%(category_abbr_en)   
    sqlcmd='SELECT data_file_info.path,data_file_info.filename FROM data_file_info INNER JOIN data_category ON data_file_info.category_id = data_category.category_id WHERE data_category.category_abbr_en = %s and start_time BETWEEN %s and %s'%(category_abbr_en,search_starttime,search_endtime)
        
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:       
        raise Exception(traceback.format_exc())  
    
    
    file_list=[]
    if(searchinfos):
        for searchinfo in searchinfos:
            path = searchinfo['path']
            filename = searchinfo['filename']                
            input_fullfilename = input_rootpath + '/' + path + '/' + filename
            ##avi图输入0大小的jpg图片会报错,但是程序不会中断
            ##OpenCV(4.2.0) /io/opencv/modules/imgproc/src/resize.cpp:4045: error: (-215:Assertion failed) !ssize.empty() in function 'resize'
            file_list.append(input_fullfilename)
            
    else:
        infos = '数据库 %s,产品 %s不存在,时间段%s %s'%(table_name,category_abbr_en,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return 
   
    ####压缩
    try:
        interact_opt.make_video.img2video(file_list,output_fullpath,fps=frame_ps)                 
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    
    return 
              

def export_partial_data(category_abbr_en,starttime,endtime,output_fullpath):
    """
    cd /home/YJY015/code;python3 /home/YJY015/code/export.py GFZ_Kp_tab '2020-06-16 00:00:00' '2020-06-18 23:59:59' /home/YJY015/test/20200616_20200618.zip
    category_abbr_en 用户传入,取数据库中查询此类数据
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_partial_data')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']         
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    table_name  = 'data_file_info'
    
    
    # s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    # s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    # s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    # s_hour    = 0    
    # s_minute  = 0
    # s_second  = 0
    
    
    # e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    # e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    # e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    # e_hour    = 23
    # e_minute  = 59
    # e_second  = 59
    
    
    search_starttime='\'%s\''%starttime
    search_endtime  ='\'%s\''%endtime
    
    
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd="SELECT * FROM %s WHERE category_abbr_en = '%s' and start_time BETWEEN %s and %s"%(table_name,category_abbr_en,search_starttime,search_endtime)
    sqlcmd="SELECT data_file_info.*, data_category.* FROM data_file_info INNER JOIN data_category ON data_file_info.category_id = data_category.category_id WHERE data_category.category_abbr_en = '%s' and data_file_info.start_time BETWEEN %s and %s"%(category_abbr_en,search_starttime,search_endtime)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    #relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            path = searchinfo['path']
            filename = searchinfo['filename']
            absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            #relative_input_fullfilename = '/' + path + '/' + filename
            absolute_path_list.append(absolute_input_fullfilename)
            #relative_path_list.append(relative_input_fullfilename)
            
    else:
        pass
        #raise Exception('数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime))
        #print ('数据库中不存在，%s' % category_abbr_en)
        # infos = sqlcmd + ' 未搜索到数据'
        # loggings.debug_log(infos)        
        # exit(0)
        infos = '数据库 %s,产品 %s不存在,时间段%s %s'%(table_name,category_abbr_en,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return 
        
    infos = '数据库表data_file_info导出数据, %d条'%len(searchinfos)
    loggings.debug_log(infos)#输出log日志里    
    
    
    try:
        interact_opt.zipCompressLst.zipCompress_data(absolute_path_list,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    infos = '收集数据%s,压缩并导出,时间段为%s,%s'%(category_abbr_en,starttime,endtime)
    loggings.debug_log(infos)#输出log日志里   
    
    return 
    
    
    
    
#def export_data(starttime,endtime,output_fullpath,json_file='data.json'):    
def export_data(starttime,endtime,output_fullpath):
    """
    1. starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    2. endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    3. output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    4. 全部导出功能,比较耗时,需要添加导出状态表,前端界面可以查询此状态,查询有效期为3天,3天过后,导出没有结束,就不处理
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_data')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']         
    
    #db_name = 'yjy015'
    db_name = configs['db_name'] 
    export_json_rootpath = configs['export_json_rootpath'] 
    table_name  = 'data_file_info'
    json_file = 'data_file_info.json'
    
    s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0
    
    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59
    
    
    search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    ####必须是select *,因为要导出所有字段
    sqlcmd='SELECT * FROM %s WHERE start_time BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)

    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    #relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            path = searchinfo['path']
            filename = searchinfo['filename']
            absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            #relative_input_fullfilename = '/' + path + '/' + filename
            absolute_path_list.append(absolute_input_fullfilename)
            #relative_path_list.append(relative_input_fullfilename)
            
    else:
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        ##exit导致整个主进程退出,后面的子函数不调用,如果data导出失败,product导出也会跳过
        #exit(0)
        return
        #raise Exception('数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime))
        #print ('数据库中不存在，%s' % category_abbr_en)
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里    
    
    
    ##数据库记录写入jason文件
    #json_file='data.jason'
    #json_fullpath = os.path.join(despath,json_file)
    #json_fullpath = os.path.join(input_rootpath,json_file)
    
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file
    
    
    ##写入data文件
    ####方案1
    # with open(json_fullpath,'w',encoding='utf-8') as f:
        # for searchinfo in searchinfos:
            # json.dump(searchinfo,f,indent=4,ensure_ascii=False)
            # #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)    
            # f.write('\n')
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        #for searchinfo in searchinfos:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))
            #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)    
            #f.write('\n')    
            
    # print (file_list)
    # input()
    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    infos = '收集数据data,压缩并导出'
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)

    return 
    
    
#def export_product(starttime,endtime,output_fullpath,json_file='product.json'):
def export_product(starttime,endtime,output_fullpath):
    #pass
    """
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_product')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']         
    #db_name = 'yjy015'
    db_name = configs['db_name']
    export_json_rootpath = configs['export_json_rootpath'] 
    
    table_name  = 'product_file_info'
    json_file='product_file_info.json'    
    
    s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0
    
    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59
    
    
    search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    sqlcmd='SELECT * FROM %s WHERE start_time BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)    
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    #relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            path = searchinfo['path']
            filename = searchinfo['filename']
            absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            #relative_input_fullfilename = '/' + path + '/' + filename
            absolute_path_list.append(absolute_input_fullfilename)
            #relative_path_list.append(relative_input_fullfilename)
            
    else:
        #pass##没有搜索到,不应该返回异常,否则前端无响应
        #raise Exception('数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime))
        #print ('数据库中不存在，%s' % category_abbr_en)
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return 
        
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里     
    
    ##数据库记录写入jason文件
    #json_file='data.jason'
    #json_fullpath = os.path.join(despath,json_file)
    #json_fullpath = os.path.join(input_rootpath,json_file)    
    #json_fullpath = export_json_rootpath + json_file
    #json_fullpath = export_json_rootpath + starttime + '/' + json_file
    
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file
    
    ##写入data文件
    ####方案1
    # with open(json_fullpath,'w',encoding='utf-8') as f:
        # for searchinfo in searchinfos:
            # json.dump(searchinfo,f,indent=4,ensure_ascii=False)
            # #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)    
            # f.write('\n')
            
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        #for searchinfo in searchinfos:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))
            #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)    
            #f.write('\n')    

            
    # print (file_list)
    # input()
    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    infos = '产品数据product,压缩并导出'
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)
        
    return 



#def export_alert(starttime,endtime,output_fullpath,json_file='alert.json'):
def export_alert(starttime,endtime,output_fullpath):
    #pass
    """
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_alert')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    
    #input_rootpath             = configs['data_rootpath']
    input_rootpath             = configs['rootpath']         
    #db_name = 'yjy015'
    db_name = configs['db_name']
    export_json_rootpath = configs['export_json_rootpath'] 
    
    table_name  = 'alert_file_info'
    json_file='alert_file_info.json'    
    
    s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0
    
    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59
    
    
    search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM %s WHERE utc_time BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)
    sqlcmd='SELECT * FROM %s WHERE bj_time BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            pass
            # path = searchinfo['path']
            # filename = searchinfo['filename']
            # absolute_input_fullfilename = input_rootpath + '/' + path + '/' + filename
            # relative_input_fullfilename = '/' + path + '/' + filename
            # absolute_path_list.append(absolute_input_fullfilename)
            # relative_path_list.append(relative_input_fullfilename)
            
    else:
        #pass
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return
        #raise Exception('数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime))
        #print ('数据库中不存在，%s' % category_abbr_en)
    
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里   

    
    ##数据库记录写入jason文件
    #json_file='data.jason'
    #json_fullpath = os.path.join(despath,json_file)
    #json_fullpath = os.path.join(input_rootpath,json_file)    
    #json_fullpath = export_json_rootpath + starttime + '/' + json_file    
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file
    
    ####方案1
    # ##写入data文件
    # with open(json_fullpath,'w',encoding='utf-8') as f:
        # for searchinfo in searchinfos:
            # json.dump(searchinfo,f,indent=4,ensure_ascii=False)
            # #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)
            # f.write('\n')
    
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        #for searchinfo in searchinfos:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))
            #json.dumps(searchinfo,f,indent=4,ensure_ascii=False)    
            #f.write('\n')    
            
            
    # print (file_list)
    # input()
    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    

    infos = '警报数据alert,压缩并导出'
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)
        
    return 



def export_report(starttime,endtime,output_fullpath):
    """
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_report')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    input_rootpath             = configs['rootpath']         
    db_name = configs['db_name'] 
    export_json_rootpath = configs['export_json_rootpath']
    
    table_name  = 'report_file_info'
    json_file='report_file_info.json'  
    
    s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0
    
    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59
    
    
    search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    sqlcmd='SELECT * FROM %s WHERE utc_date_end BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            pass
            
    else:
        #pass
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return
    
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里   

    
    ##数据库记录写入jason文件
    #json_fullpath = os.path.join(input_rootpath,json_file)    
    #json_fullpath = export_json_rootpath + starttime + '/' + json_file           
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file
    
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))

    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    

    infos = '报告数据report,压缩并导出'
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)
        
    return 




def export_event_configuration(starttime,endtime,output_fullpath):
    """
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    loggings=Loggings(log_starttime,'export_event_configuration')
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    input_rootpath             = configs['rootpath']         
    db_name = configs['db_name']
    export_json_rootpath = configs['export_json_rootpath']
    
    table_name  = 'event_configuration'
    json_file='event_configuration.json'  
    
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    sqlcmd='SELECT * FROM %s'%(table_name)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            pass
            
    else:
        #pass
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return
    
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里   

    
    ##数据库记录写入jason文件
    #json_fullpath = os.path.join(input_rootpath,json_file)    
    #json_fullpath = export_json_rootpath + starttime + '/' + json_file          
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file    
    
    
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))

    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    

    infos = '事件等级配置表event_configuration,压缩并导出'
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)
        
    return 


def export_element_table(elment_tablename,starttime,endtime,output_fullpath):
    """
    starttime格式最好是 2020-05-27 00:00:00 ，可以直接去数据库里查找
    endtime 格式最好是 2020-05-27 23:59:59 ，可以直接去数据库里查找
    output_fullpath输出全路径，包括文件名称，比如/home/YJY015/data/20200527.zip
    
    """
    
    log_starttime  = get_current_BJT()    
    ####实例化日志类
    #loggings=Loggings(log_starttime,'export_element_ace_ep')
    loggings=Loggings(log_starttime,elment_tablename)    
    
    despath,name = os.path.split(output_fullpath)
    if not os.path.exists(despath):
        os.makedirs(despath)
    
    input_rootpath             = configs['rootpath']         
    db_name = configs['db_name']
    export_json_rootpath = configs['export_json_rootpath']
    
    #table_name  = 'element_ace_ep'
    table_name  = elment_tablename     
    #json_file='element_ace_ep.json' 
    json_file= elment_tablename + '.json' 
    
    
    s_year    = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
    s_month   = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
    s_day     = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
    s_hour    = 0    
    s_minute  = 0
    s_second  = 0
    
    
    e_year    = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
    e_month   = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
    e_day     = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
    e_hour    = 23
    e_minute  = 59
    e_second  = 59
    
    
    search_starttime='\'%s\''%datetime.datetime(s_year,s_month,s_day,s_hour,s_minute,s_second).strftime('%Y-%m-%d %H:%M:%S')
    search_endtime  ='\'%s\''%datetime.datetime(e_year,e_month,e_day,e_hour,e_minute,e_second).strftime('%Y-%m-%d %H:%M:%S')
    #sqlcmd='SELECT path,filename FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    #sqlcmd='SELECT * FROM data_file_info WHERE start_time BETWEEN %s and %s'%(search_starttime,search_endtime)
    sqlcmd='SELECT * FROM %s WHERE utc_time BETWEEN %s and %s'%(table_name,search_starttime,search_endtime)
    
    pga=PostgresArchive()
    try:
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)           
        #print (searchinfos)
    except Exception as e:
        raise Exception(traceback.format_exc())
    
    
    absolute_path_list=[]##磁盘上存放的绝对路径
    #relative_path_list=[]##数据库中的相对路径
    if(searchinfos):
        for searchinfo in searchinfos:
            pass
            
    else:
        #pass
        infos = '数据库 %s,产品不存在,时间段%s %s'%(table_name,starttime,endtime)
        loggings.debug_log(infos)#输出log日志里       
        #raise Exception(infos)
        #exit(0)
        return
    
    infos = '数据库表%s 导出数据, %d条'%(table_name,len(searchinfos))
    loggings.debug_log(infos)#输出log日志里   
    
    ##数据库记录写入jason文件
    #json_fullpath = os.path.join(input_rootpath,json_file)    
    #json_fullpath = export_json_rootpath + starttime + '/' + json_file  
    export_json_path = export_json_rootpath + starttime + '/'
    if not os.path.exists(export_json_path):
        os.makedirs(export_json_path)    
    json_fullpath =  export_json_path + json_file    
    
    
    ####方案2
    with open(json_fullpath,'w',encoding='utf-8') as f:
        f.write(json.dumps(searchinfos,indent=4,ensure_ascii=False))

    ####压缩
    try:
        interact_opt.zipCompressLst.zipCompress(absolute_path_list,json_fullpath,output_fullpath)                  
    except Exception as e:
        #loggings.debug_log(str(e))                  #输出异常操作到log日志里
        #loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
        #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
        raise Exception(traceback.format_exc())    
    
    
    #infos = 'element_ace_ep,压缩并导出'
    infos = '%s,压缩并导出'%table_name
    loggings.debug_log(infos)#输出log日志里   
    
    ##json临时文件，在压入zip文件之后，可以删除
    ##判断文件是否存在，存在删除，不存在跳过，如果不存在，使用remove，系统报错 FileNotFoundError: [Errno 2] No such file or directory:
    
    # if not os.path.exists(json_fullpath):
        # pass
    # else:
        # os.remove(json_fullpath)
        
    # infos = ''
    # loggings.debug_log(infos)#输出log日志里          
    return 


def clean_up_export_dir():
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    #filepath = configs['export_rootpath']
    
    ####内网机需要配置共享磁盘根路径
    filepath = configs['export_rootpath']    
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
    if (len(sys.argv) == 4):
        argv0 = sys.argv[0]
        argv1 = sys.argv[1]
        argv2 = sys.argv[2]
        argv3 = sys.argv[3]
        
        ##每次进入export功能,执行一次/home/YJY015/export/目录清除,导出前需要清除,如果导出后进行清除,导致java程序到export找不到文件
        clean_up_export_dir()
        #input()
        
        filesize = 0 ##初始大小为0
        
        try:
            ##如果存在压缩文件夹,首先需要删除,否则影响后面追加文件的正确性
            if os.path.exists(argv3):
                os.remove(argv3)
                print ('存在%s,需要清理掉.'%argv3)
            
            starttime   = argv1
            endtime     = argv2
            s_year      = datetime.datetime.strptime(starttime, "%Y-%m-%d").year
            s_month     = datetime.datetime.strptime(starttime, "%Y-%m-%d").month
            s_day       = datetime.datetime.strptime(starttime, "%Y-%m-%d").day
            s_hour      = 0
            s_minute    = 0
            s_second    = 0        
            e_year      = datetime.datetime.strptime(endtime, "%Y-%m-%d").year
            e_month     = datetime.datetime.strptime(endtime, "%Y-%m-%d").month
            e_day       = datetime.datetime.strptime(endtime, "%Y-%m-%d").day
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
                print ('之前有过此时间段的导出操作,不需要再进行导出操作,需要继续导致,可以继续导出')
                #return ##之前有过此时间段的删除操作,不需要再进行删除操作
            if 1==ret_code:
                print ('之前有过此时间段的导出操作,但是status状态为False,需要再进行一次导出操作')
                #pass ##之前有过此时间段的删除操作,但是status状态为False,需要再进行一次删除操作
            if 2==ret_code:
                print ('之前没有此时间段的导出操作,需要插入初始状态记录')
                record_time  = get_current_BJT()   
                update_time  = get_current_BJT()  
                status='False'        
                record_db(record_time,update_time,start_time,end_time,status,filesize) ##之前没有此时间段的删除操作,需要插入初始状态记录 
        
            ##压缩收集到的数据及其数据库记录导出到json文件
            export_data(argv1,argv2,argv3)
            print ('export_data finish.')
            ##压缩要素提取生成的产品及其数据库记录导出到json文件
            export_product(argv1,argv2,argv3)    
            print ('export_product finish.')            
            ##发送警报的短信导出到json文件
            export_alert(argv1,argv2,argv3)
            print ('export_alert finish.')            
            ##发送警报报告导出到json文件
            export_report(argv1,argv2,argv3)
            print ('export_report finish.')            
            
            ##export_element导出到json文件
            elment_tablename_list = ['element_ace_ep','element_ace_mag','element_ace_sis','element_ace_sw','element_ap','element_dst',
                                     'element_f107','element_goes_ie','element_goes_ip','element_goes_mag','element_goes_xr','element_hpi',
                                     'element_kp','element_rad','element_ssn','element_ste_het','element_ste_mag','element_ste_sw',
                                     'element_swpc_flare','element_tec']
            for elment_tablename in elment_tablename_list:
                export_element_table(elment_tablename,argv1,argv2,argv3)
                print ('export_element_table finish.') 
            ##event_configuration导出到json文件
            export_event_configuration(argv1,argv2,argv3)            
            print ('export_event_configuration finish.')             
            
            
            ####获取文件大小
            filesize = os.path.getsize(argv3)
            filesize_MB = int(filesize/1024/1024)
            
            ####更改数据导出的监控状态
            update_time  = get_current_BJT()
            config_infos={
                        'update_time':update_time,
                        'status':'True',
                        'filesize':filesize_MB}#配置更新之后的值
            # condition_infos={             
                        # 'start_time':start_time,
                        # 'end_time':end_time,
                        # 'status':'False'} 
            ####true,false状态,都需要更新
            condition_infos={             
                        'start_time':start_time,
                        'end_time':end_time}                         
            update_db(config_infos,condition_infos)  
        
        except Exception as e:
            ##如果异常,UI界面如何获取异常
            raise Exception(traceback.format_exc())   
        

            
    elif (len(sys.argv) == 7):
        argv0 = sys.argv[0] #主程序export.py 
        argv1 = sys.argv[1] #数据英文标识
        argv2 = sys.argv[2] #开始时间   
        argv3 = sys.argv[3] #结束时间 
        argv4 = sys.argv[4] #帧数
        argv5 = sys.argv[5] #格式  .avi或者.gif
        argv6 = sys.argv[6] #输出全路径
        
        print ('argv0 = %s'%argv0)
        print ('argv1 = %s'%argv1)
        print ('argv2 = %s'%argv2)
        print ('argv3 = %s'%argv3)
        print ('argv4 = %s'%argv4)
        print ('argv5 = %s'%argv5)
        print ('argv6 = %s'%argv6)
        
        if argv5=='.gif':
            try:
                export_gif(argv1,argv2,argv3,float(argv4),argv6)
            except Exception as e:
                ##如果异常,UI界面如何获取异常
                raise Exception(traceback.format_exc())
        
        if argv5=='.avi':
            try:
                export_avi(argv1,argv2,argv3,float(argv4),argv6)
            except Exception as e:
                ##如果异常,UI界面如何获取异常
                raise Exception(traceback.format_exc())        
        
        
    elif (len(sys.argv) == 5):
        argv0 = sys.argv[0]##python脚本全路径
        argv1 = sys.argv[1]##英文标识
        argv2 = sys.argv[2]##开始时间,UTC,格式yyyy-mm-dd HH:MM:SS
        argv3 = sys.argv[3]##结束时间,UTC,格式yyyy-mm-dd HH:MM:SS
        argv4 = sys.argv[4]##导出zip文件压缩包全路径,不包含json文件,本功能针对用户自己查看文件，并不进行导入功能
        
        try:
            ##如果存在压缩文件夹,首先需要删除,否则影响后面追加文件的正确性
            if os.path.exists(argv4):
                os.remove(argv4)
                
            ##压缩收集到的数据
            export_partial_data(argv1,argv2,argv3,argv4)
         
         
        except Exception as e:
            ##如果异常,UI界面如何获取异常
            raise Exception(traceback.format_exc())         
        
        
        