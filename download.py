#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
2020-05-08 17:33:04
                    1. 自动下载功能，定时启动，需要linux的crontab，但是crontab不能针对每种数据，做专门的调度任务
                    2. 如果针对140种数据，需要些140个shell脚本，配置到crontab里，140条crontab记录
                    3. 手动下载功能，配合apsheduler调用模块，在配合后台启动，再配合开机启动脚本，保证掉电后，可以自动重启
                    
2020-05-09 10:15:22
                    1. main函数作为主函数，如果上层有调度任务调用，程序里最好使用raise，可以被上层调用捕获异常，不要用exit退出
                    
2020-05-12 09:37:39
                    1. ops_data,删除每天的临时数据，需要拼接数据的根路径
                    2. 要素提取的状态，默认不去查找，不论是true还是false，都更新

2020-06-10 17:21:09 
                    1. 历史数据下载，命令行传递参数
                    
"""


import os
import sys
import datetime
import traceback


from db.postgres_table import *
from db.postgres_archive import *


from file_info.wget_download import WgetDownload

from element_opt.element_extract import *           ##要素提取
from element_opt.element_record import *            ##入库

from logger.logger import *
from io_interface.io_stat import *

from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_current_BJT
from cfg.conf import *
from sys_interface.sys_std import *
from sys_interface.sys_str import *



def download_wget_manually(category_abbr_en,starttime,endtime,searchinfos):
    """
    输入的时间，都是UTC时间
    """
    #print ('download_wget_manually......!')
    ##获取系统当前时间，截取YYYYMMDD即可，1次启动，永久运行，直到人工停止
    ####解析数据库，得到url信息
    url=[]
    for searchinfo in searchinfos:
        #print (searchinfo)
        url = searchinfo['url']
        ####searchinfo返回的是字典
        #category_id = searchinfo['category_id']
        f_print ('url = %s'%url)
        #print ('category_id = %d'%int(category_id))
        
        wg = WgetDownload(datatype=category_abbr_en, searchinfo=searchinfo)
        #db_infos=hw.download_file(starttime,endtime) ####传入时间，与系统时间比较，如果大于系统时间(有bug,系统时间错误，就是bug)
        try:
            wg.start(starttime,endtime) ####传入时间，与系统时间比较，如果大于系统时间(有bug,系统时间错误，就是bug)
        except Exception as e:
            raise Exception(traceback.format_exc())     

    #return db_infos
    ####每天自动下载，最好是按UTC时间0点启动，北京时间就是08:00:00
    ####遍历下载，根据优先级高的，先下载，优先级1>2>3
    ####排出优先级，再根据1天下载的频次，启动下载时间为每天的00：00：00，根据这个时间计算出下载频次之间的时间间隔
    ####做成类似crontab的启动任务，到点自动下载
    
    ####目前默认删除前1天的临时数据，如果今天网络中断了1天，昨天的数据就无法删除了，因为明天只会删除今天的
    ####是否增加删除前1周，或者前1个月的临时数据
    ####每次启动自动下载,针对某个数据,只保留当天时间最大的数据
    ####%Y%m%d%H%M%S转换为%Y-%m-%d %H:%M:%S，保证和数据库里格式一致，查询方便

    #return True
    return
    
    
if __name__ == "__main__":
    
    
    ####获取系统时间
    taskStarttime = get_current_BJT()
    
    
    #### 1.启动数据库 sudo service postgresql start
    #### 2.查看host配置IP是否正确，ifconfig -a
    
    
    ####分2种情况，手动下载和自动下载
    ####自动下载：命令行没有参数，获取当前的系统时间，来进行下载任务，可以开线程池，也可以串行下载
    ####手动下载：命令行传入开始时间，结束时间，数据标识;手动下载多个，需要根据优先级排列出队伍，先下载优先级高的，如果并行下载，就没有优先级的概念了；
    
    
    ####手动下载命令行
    #python3 /home/hffan/fanhuifeng/python_prj/YJY015/sqlmain.py CDA_TIMED_SL2b 20190919111000 20190920111000
    ####自动下载命令行
    #python3 /home/hffan/fanhuifeng/python_prj/YJY015/sqlmain.py
    
    
    ########可以使用navicat手动创建库和表；也可以使用python语句创建数据库和表
    ########创建psql数据库，建立数据库
    
    
    ####自动下载，手动下载的参数都不符合，报错
    if (len(sys.argv) != 2 ) and (len(sys.argv) != 4 ):
        f_print('请输入正确的命令行参数')
        f_print('自动下载功能：') 
        f_print('     第1个参数：主程序,名称为 %s' % os.path.basename(__file__))
        f_print('     第2个参数：下载数据英文标识，参考file_info_db数据库中data_category表中category_abbr_en字段')

        f_print('手动下载功能：') 
        f_print('     第1个参数：主程序,名称为 %s' % os.path.basename(__file__))
        f_print('     第2个参数：下载数据英文标识，参考file_info_db数据库中data_category表中category_abbr_en字段')        
        f_print('     第3个参数：下载数据文件中UTC时间，格式yyyymmddHHMMSS, 比如 20200318192100')   
        f_print('     第4个参数：下载数据文件中UTC时间，格式yyyymmddHHMMSS, 比如 20200318192100')
        raise Exception('请输入正确的命令行参数')
        #exit()       
    
    
    ####手动下载
    elif(len(sys.argv)==4):
        f_print('sys.argv[0] = %s'%sys.argv[0])  
        f_print('sys.argv[1] = %s'%sys.argv[1])  
        f_print('sys.argv[2] = %s'%sys.argv[2])  
        f_print('sys.argv[3] = %s'%sys.argv[3])   
        
        exe = sys.argv[0]
        category_abbr_ens=sys.argv[1]           
        starttime=sys.argv[2]                   ####时间格式20191008144500，因为命令行不能有空格，否则会认为是2个参数
        endtime=sys.argv[3]                     
        
        
        #db_name = 'yjy015'
        db_name = configs['db_name']
        table_name  = 'data_category'
        ####拆分不同的数据类型
        category_abbr_ens_list = category_abbr_ens.split(',')
        for category_abbr_en in category_abbr_ens_list:
            
            taskType=category_abbr_en
            loggings=Loggings(taskStarttime,taskType)#实例化日志类        
            ########查询数据库
            ########测试入库方法
            pga=PostgresArchive()
            category_abbr_en=category_abbr_en
            cdt_element={"category_abbr_en":category_abbr_en}
            try:
                #searchinfos=pga.search_db_table('file_info_db','data_category',cdt_element)            
                searchinfos=pga.search_db_table(db_name,table_name,cdt_element)
                #print (searchinfos)
            except Exception as e:
                loggings.debug_log(str(e))                      #输出异常操作到log日志里
                loggings.debug_log(traceback.format_exc())      #输出堆栈异常到log日志里
                #exit(traceback.format_exc())                   #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                
                raise Exception(traceback.format_exc())
            
            if(searchinfos):
                try:
                    #download_manually(category_abbr_en,starttime,endtime,searchinfos)
                    download_wget_manually(category_abbr_en,starttime,endtime,searchinfos)                                        
                    f_print ('download_wget_manually 下载完成')
                except Exception as e:
                    loggings.debug_log(str(e))                  #输出异常操作到log日志里
                    loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
                    #exit(traceback.format_exc())               #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态                    
                    raise Exception(traceback.format_exc())            
            else:
                f_print ('数据库data_category 中不存在数据类型%s，请检查核对配置表.'%category_abbr_en)
             

    #db_name = 'yjy015'
    db_name = configs['db_name']  
    table_name  = 'data_category'    
    #### 2.     
    #### 先从数据库里查，file_info表中是否有category_abbr_en入库的数据
    #print ('%s%s%s%s' % ('FILE: ',__file__, ',LINE: ', sys._getframe().f_lineno))
    category_abbr_ens_list = category_abbr_ens.split(',')
    for category_abbr_en in category_abbr_ens_list:
        pga=PostgresArchive()
        
        #### 2.1
        #### 先查category_abbr_en对应的category_id
        condition_element={"category_abbr_en":category_abbr_en}
        try:
            #searchinfos=pga.search_db_table('file_info_db','data_category',condition_element)        
            searchinfos=pga.search_db_table(db_name,table_name,condition_element)
            f_print (searchinfos)
            
            ##category只能搜到1条配置记录
            element_extract_flag = searchinfos[0]['element_extract_flag']#查找配置信息表里，某数据对应的要素提取标识            
            #element_extract_flag = searchinfos['element_extract_flag']#查找配置信息表里，某数据对应的要素提取标识
        except Exception as e:
            loggings.debug_log(category_abbr_en)        #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
            #exit(traceback.format_exc())               #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态            
            raise Exception(traceback.format_exc())        
        if(searchinfos):
            category_id = searchinfos[0]['category_id']#取searchinfo列表里第1个元素            
            category_abbr_en = searchinfos[0]['category_abbr_en']
            
            #category_id = searchinfos['category_id']#取searchinfo列表里第1个元素            
            f_print ('配置表data_category 数据库中存在, category_abbr_en,category_id = %s %s'%(category_abbr_en,category_id))
        else:
            err = '配置表data_category 数据库中不存在, category_abbr_en,category_id = %s %s'%(category_abbr_en,category_id)
            f_print (err)
            raise Exception(err)         
        
        
        table_data_file_info = 'data_file_info'
        #### 2.2
        #### 查file_info库里是否有category_id, starttime,state = true的成功入库的记录
        # condition_element={ 'category_id':category_id,
                            # 'start_time':datetime.datetime.strptime(starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S'),
                            # 'state':'True'}
        condition_element={ 'category_abbr_en':category_abbr_en,
                            'start_time':datetime.datetime.strptime(starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S'),
                            'state':'True'}
                            
        try:
            #searchinfos=pga.search_db_table('file_info_db','file_info',condition_element)
            searchinfos=pga.search_db_table(db_name,table_data_file_info,condition_element)            
            f_print (searchinfos)
        except Exception as e:
            loggings.debug_log(str(e))                  #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())  #输出堆栈异常到log日志里
            #exit(traceback.format_exc())               #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态            
            raise Exception(traceback.format_exc())                
        if(searchinfos):
            f_print ('数据库data_file_info 中存在,category_abbr_en,start_time,state = %s %s %s'%(category_abbr_en,starttime,'True'))
            ##获取数据库中存储文件存储全路径
            #category_id= searchinfos[0]['category_id']
            category_abbr_en= searchinfos[0]['category_abbr_en']            
            path = searchinfos[0]['path']#取searchinfo列表里第1个元素
            filename = searchinfos[0]['filename']#取searchinfo列表里第1个元素
            element_storage_status = searchinfos[0]['element_storage_status']
            record_time= searchinfos[0]['record_time']
            start_time= searchinfos[0]['start_time']
            end_time= searchinfos[0]['end_time']
            file_size= searchinfos[0]['file_size']
            state= searchinfos[0]['state']
            log= searchinfos[0]['log']            
        else:
           f_print ('数据库data_file_info 中不存在,category_abbr_en,start_time,state = %s %s %s'%(category_abbr_en,starttime,'True'))
           f_print ('数据收集操作失败，暂时不需要要素提取，不需要要素入库，不需要更新element_storage_status的状态.')
           continue#如果数据收集，不存在此数据，不需要数据提取
        
        
        #### 3. todo
        ####要素提取之前,检查数据类型是否需要要素提取
        #if category_abbr_en not in element_extract_datatypes:
        #if int(element_extract_flag) == 0:
        if element_extract_flag == 'False':        
            f_print ('category_abbr_en = %s 不在要素提取数据种类里，不需要进行要素提取操作.'%(category_abbr_en))
            continue
        
        
        #### 4. 
        #### 要素提取入库
        ##提取之前，先检查element_storage_status如果已经提取过，就continue
        ##element_storage_status为True，也有未真正要素提取入库，却把element_storage_status更新为True的情况
        
        ####默认都要素提取，直接覆盖
        # if('True'==element_storage_status):
            # print('%s %s %s %s'%(filename,'element_storage_status = ',element_storage_status,'要素提取状态为true，之前已经完成要素提取操作，所以不需要要素提取......'))
            # continue
        
        el_ext = ElementExtract(datatype=category_abbr_en,path=path,filename=filename)   #实例化 要素提取类
        try:
            el_re = ElementRecord(datatype=category_abbr_en)        #实例化 要素提取入库类
        except Exception as e:
            loggings.debug_log(str(e))                              #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())              #输出堆栈异常到log日志里
            #exit(traceback.format_exc())                           #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态            
            raise Exception(traceback.format_exc())        
        try:
            table_name = el_re.get_table_name()
        except Exception as e:
            loggings.debug_log(str(e))                      #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())      #输出堆栈异常到log日志里
            #exit(traceback.format_exc())                   #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态        
            raise Exception(traceback.format_exc())        
        #### 需要判断每个表对应英文标识
        dict_data1,dict_data2= el_ext.get_data()
        # f_print('dict_data1 = %s'%dict_data1)
        # f_print('dict_data2 = %s'%dict_data2)
        #input()
                
        try:
            el_re.record(table_name,starttime,dict_data1,dict_data2)
        except Exception as e:
            loggings.debug_log(str(e))                   #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())   #输出堆栈异常到log日志里
            #exit(traceback.format_exc())                #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态
            raise Exception(traceback.format_exc())        
        f_print ('%s 要素提取入库完成.'% table_name[0])
        
        
        #### 5.
        #### 不需要检查element_storage_status的状态，第2步已经检查过，此处element_storage_status一定是False
        #### 先查要素提取入库是否成功，成功需要更改element_storage_status子段，不成功，不需要更改
        #### 需要更改file_info数据库file_info表里对应的category_abbr_en，starttime的表中的element_storage_status状态
        #### 先需要判断element_storage_status为1，说明已经提取要素入库了，不需要更新，因为有重复下载导致重复更新element_storage_status状态的情况
        #### 更新，要求config_infos唯一，否则可能出错
        #### kp，ap共用1个html文件，更新1次状态即可
        #### 可能存在假入库的情况，如果要素提取入库失败，程序还正常运行，导致把element_storage_status状态错误更新成True
        #### 
        config_infos={'element_storage_status':True}
        #### condition的条件，可以区分是哪一种数据即可
        # condition_infos={                    
                    # 'category_id':category_id,
                    # 'filename':filename,
                    # 'path':path,
                    # 'element_storage_status':False}##更新要素提取element_storage_status状态
        ####默认都更新element_storage_status状态
        # condition_infos={                    
                    # 'category_id':category_id,
                    # 'filename':filename,
                    # 'path':path}##更新要素提取element_storage_status状态
        condition_infos={                    
                    'category_abbr_en':category_abbr_en,
                    'filename':filename,
                    'path':path}##更新要素提取element_storage_status状态
        try:
            #pga.update_db_table('file_info_db','file_info',config_infos,condition_infos)         
            pga.update_db_table(db_name,table_data_file_info,config_infos,condition_infos)          
            f_print ('%s element_storage_status 更新完成完成.'% filename)
        except Exception as e:
            loggings.debug_log(str(e))                      #输出异常操作到log日志里
            loggings.debug_log(traceback.format_exc())      #输出堆栈异常到log日志里
            #exit(traceback.format_exc())                   #异常直接退出，否则可能出现没有element的数据库，但是提示要素提取完，并且把element_storage_status状态更新为true的状态            
            raise Exception(traceback.format_exc())    
    
    