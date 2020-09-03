# -*- coding: utf-8 -*-


"""
@modify history
2020-05-06 11:26:26 
                    1. 修改http_stage3_datatype1类型里localfilename，截取日期的bug
                    
                    
2020-05-08 14:59:10
                    1. 写文件，使用绝对路径，需要从cfg配置文件里读取绝对路径的根路径
                    2. 入库，只需要入相对路径即可，UI界面，在tomcat里配置绝对路径的根路径
 
2020-05-14 16:13:12 
                    1. python第3方库wget很多数据下载失败，使用linux命名wget
                    2. linux需要安装wget包
                    3. data_file_info只入成功的数据，失败的数据都不录入数据库中，失败的任务只在调度任务表里体现
                    4. 需要实现远程和本地文件大小比较，否则有可能下的数据不全
                    5. 下载list判别
                    
2020-05-15 13:20:32
                    1. wget参数介绍
2020-05-19 12:17:23
                    1. 网站路径，根据年自动变化
2020-05-20 09:35:15
                    1. excel表格里的正则匹配，'--accept acclist'
2020-05-27 15:58:33
                    1. localfilename_timestamp，调度有1-2秒的容错，导致utc时间不是整点，需要把文件名按整点时刻命名
2020-05-28 12:14:27
                    1. 入库报错,使用str(e),写日志可以写raise Exception(traceback.format_exc())  
2020-06-01 11:30:54
                    1. self.db_path = '/' + configs['dataname'] + '/' + self.save_path
                    2. db_path数据库入库目录，带data文件夹，save_path从excel表格读取，没有data文件夹
2020-06-01 13:13:00
                    1. 第9个数据, 后缀名jpg，配置表data_category配置的suffix为png导致程序下载判断匹配失败，进而导致数据下载失败
                    2. --accept 20200528_*_NL*.jpg,2020528_*_NL*.jpg，需要特殊处理，202005，20205，月份可能有05，5的情况
                    
2020-06-10 18:18:43
                    1. 新增data_monitor任务监控表，根据下载数据是否存在，来判断任务是否成功
                    2. 模糊匹配，下载成功的记录，有可能重复，因为根据文件存在与否判断，可能文件是上1次下载的
                    3. 模糊匹配，下载失败的记录，一定是失败，因为文件不存在，一定是失败的
                    4. 直接拼接文件名，下载的任务，成功的一定是成功的，失败的一定是失败的
                    
"""


import subprocess
import os
import re
import traceback
import datetime
import time
import wget

from logger.logger import *
from db.postgres_table import *
from db.postgres_archive import *
from cfg.conf import *
from sys_interface.sys_std import *
from sys_interface.sys_str import *

from time_interface.time_format import get_current_UTC
from time_interface.time_format import get_current_BJT


class WgetDownload:
    # 初始化
    def __init__(self,datatype,searchinfo):
        ####增加数据库名统一配置，可以放到conf配置文件里
        
        self.datatype = datatype            # 下载数据类型
        self.searchinfo=searchinfo          # 数据库查询信息
        self.category_id=0                  # 数据库查询到的id
        self.category_abbr_en = ''
        self.url = ''                       # 实时网址
        self.full_url = ''                  # wget下载，拼接网址和文件的全链接
        self.download_filename = ''         # 下载文件名
        self.regular_expression = ''        # 正则表达式匹配规则
        self.save_path = ''                 # 归档路径
        self.suffix = ''                    # 格式
        self.url_date_flag = ''             # url包含日期、
        self.starttime = ''                 # 下载配置的开始时间
        self.endtime = ''                   # 下载配置的结束时间
        self.localfilename = ''             # 存储文件名
        self.localfilename_timestamp = ''   # 存储文件名追加时间
        
        self.downloadfullpathname  = ''     # 改名之前的全路径加文件名
        self.localfullpathname  = ''        # 改名之后的全路径加文件名
        self.localfullpath      = ''


        
        ####归档入库的所有全局变量定义，加db前缀
        ####如果数据下载失败，使用此全局变量入库
        self.db_category_abbr_en = ''
        self.db_category_id=0
        self.db_filename=''
        self.db_path=''
        self.db_record_time=''
        self.db_start_time=''
        self.db_end_time=''
        self.db_file_size=0
        self.db_state=False
        self.db_log='失败'                          ####全局变量，可以在程序中使用此变量，记录实际的错误信息
        self.db_element_storage_status=False        ####全局变量，要素提取入库成功之后，需要更新状态为True
        
        self.data_class     = ''
        self.research_area  = ''
        self.website        = ''
        
        return


    def get_midssxx(self,midsxx,yyyy):
        mids=re.findall(r'\D+',midsxx)[0]       ##查找到的是list，需要转换成str
        index=re.findall(r'\d+',midsxx)[0]      ##查找到的是list，需要转换成str
        ##以2019年为基准，进行加减运算
        sub = int(yyyy) - int(2019)
        #print (sub)
        index_s = str(int(index) + sub).zfill(2)
        #print (index_s)
        midsxx_s = mids + index_s
        #print (midsxx_s)
        return midsxx_s   

    
    def get_DOY(self,year,month,day):
        import calendar
        months=[0,31,59,90,120,151,181,212,243,273,304,334]#每个月对应的天数
        if 0<month<=12:
            DOY=months[month-1]
        else:
            f_print('month error.')
        DOY+=day
        leap=0
        #判断平年闰年
        check_year=calendar.isleap(year)
        if check_year == True:
            DOY+=1           
        #return DOY
        return '%03d'%DOY

    ##数据库dict里获取各个字段的信息
    def get_sql_info(self): 
        self.category_id            = self.searchinfo['category_id']
        self.db_category_id         = self.category_id
        self.category_abbr_en       = self.searchinfo['category_abbr_en']
        self.db_category_abbr_en    = self.category_abbr_en 
        
        self.category_name_zh = self.searchinfo['category_name_zh']

        
        self.url = self.searchinfo['url']
        self.download_filename = self.searchinfo['download_filename']
        self.regular_expression = self.searchinfo['regular_expression']         
        self.save_path = self.searchinfo['save_path']
        self.suffix = self.searchinfo['suffix']   
        self.url = self.searchinfo['url']
        self.url_date_flag = self.searchinfo['url_date_flag']         


        ####针对下载数据监控,需要如下变量
        self.data_class= self.searchinfo['data_class']
        self.research_area= self.searchinfo['research_area']
        self.website= self.searchinfo['website']
     
                    
        return

        
    ##数据入库
    def record_db(self):
        #db_name     = 'yjy015'
        db_name = configs['db_name']
        table_name  = 'data_file_info'


        pga=PostgresArchive()
        config_infos={
                    'category_id':self.db_category_id,
                    'category_abbr_en':self.db_category_abbr_en,                    
                    'filename':self.db_filename,
                    'path':self.db_path,
                    'record_time':self.db_record_time,
                    'start_time':self.db_start_time,
                    'end_time':self.db_end_time,
                    'file_size':self.db_file_size,
                    'state':self.db_state,
                    'log':self.db_log,
                    'element_storage_status':self.db_element_storage_status}
        #pga.insert_db_table('file_info_db','file_info',config_infos)
        pga.insert_db_table(db_name,table_name,config_infos)    
    
    
        # ##核对数据库里是否存在此数据，
        # ##category_id,filename相同，就是同1个数据;或者数据库为空和2个条件不全满足的可以入库 
        # def check_db(self):
            # """
            # 1. 正则表达式匹配到的文件和数据库里剔除_YYYYMMDD_hhmmss之后剩余的文件名比较是否一致
            # 2. 
            
            
            # """
            # db_name     = 'yjy015'
            # table_name  = 'data_file_info'
            
            # print ('check_db......')
            # #print (self.localfilename)
            # self.db_filename=self.localfilename
            
            # pga=PostgresArchive() 
            # #if self.datatype in http_stage4_datatype1:
            # if self.category_abbr_en == 'CDA_TIMED_SL2b' or self.category_abbr_en == 'CDA_TIMED_SL1b':
                # ####转换成datetime
                # SUTC=datetime.datetime.strptime(self.db_start_time,"%Y-%m-%d %H:%M:%S").replace(hour=0,minute=0,second=0)
                # EUTC=datetime.datetime.strptime(self.db_end_time,"%Y-%m-%d %H:%M:%S").replace(hour=23,minute=59,second=59)
                            
                # ####datetime转换成string
                # ####字符串添加单引号2019-06-16 00:12:00变成'2019-06-16 00:12:00'
                # ####格式化输出\'\'，转义字符\
                # SUTC_str='\'%s\''%SUTC.strftime("%Y-%m-%d %H:%M:%S")
                # EUTC_str='\'%s\''%EUTC.strftime("%Y-%m-%d %H:%M:%S")
                # splits = filename.split('_')
                # XXXXX=splits[2]##编号
                # XXXXX_str = '\'%s%s%s\''%('%',XXXXX,'%')
                # ####查询当天下载入库的数据里，有没有filename
                # #sqlcmd='SELECT * FROM file_info WHERE category_id = %s and start_time BETWEEN %s and %s and filename like %s'%(self.db_category_id,SUTC_str,EUTC_str,XXXXX_str)
                # sqlcmd='SELECT * FROM %s WHERE category_id = %s and start_time BETWEEN %s and %s and filename like %s'%(table_name,self.db_category_id,SUTC_str,EUTC_str,XXXXX_str)
                            
                # searchinfos=pga.search_db_table_usercmd('file_info_db',sqlcmd)
                # if(searchinfos):#数据库不为空
                    # searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
                    # state = searchinfo['state']
                    # ###名称不一样，只需要看XXXXX是否一样，filename==self.db_filename
                    # if (state=='True'):
                        # #print ('return 0')
                        # return 0
                    # elif (state=='True'):
                        # #print ('return 1')
                        # return 1                   
                # else:
                    # #print ('return 2')
                    # return 2
                    
            # else:
                # print ('数据库检查下载文件是否存在')
                # condition_element={ 'category_id':self.db_category_id,
                                    # 'filename':self.db_filename}
                # #searchinfos=pga.search_db_table('file_info_db','file_info',condition_element)
                # searchinfos=pga.search_db_table(db_name,table_name,condition_element)            

                # print (searchinfos)
                # if(searchinfos):#数据库不为空
                    # searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
                    # category_id = searchinfo['category_id']
                    # filename = searchinfo['filename']
                    # state = searchinfo['state']
                    
                    # ##state是字符串,不是BOOL类型
                    # print ('state = %s'%state)
                    # print ('category_id = %s'%category_id)
                    # print ('db_category_id = %s'%self.db_category_id)
                    # print ('filename = %s'%filename)
                    # print ('db_filename = %s'%self.db_filename)
                    # ####category_id比较多余的，因为查询数据库的时候，就是按category_id查询的
                    # #if(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='True'):                
                    # if (filename==self.db_filename) and (state=='True'):
                        # #print ('return 0')
                        # return 0
                    # #elif(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='False'):                    
                    # elif (filename==self.db_filename) and (state=='False'):
                        # #print ('return 1')
                        # return 1
                    # # elif (filename==self.db_filename) and (state=='True') and ():
                        # # print ('return 1')
                        # # return 1                
                    # ####这种情况不存在，因为查询的时候，是filename，category_id同时为查询条件
                    # # elif(category_id!=self.db_category_id) or (filename!=self.db_filename):
                        # # print ('return 2')
                        # # return 2
                # else:
                    # #print ('return 2')
                    # return 2


    def check_db(self,check_name):
        """
        1. 正则表达式匹配到的文件和数据库里剔除_YYYYMMDD_hhmmss之后剩余的文件名比较是否一致
        2. 遍历文件夹的文件名和数据库文件名比较，如果有，跳过
        3. 下载文件名
        
        
        """
        #db_name     = 'yjy015'
        db_name = configs['db_name']        
        table_name  = 'data_file_info'
        
        #f_print('check_db......')
        #print (self.localfilename)
        #self.db_filename=self.localfilename
        #self.db_filename=check_name
        
        pga=PostgresArchive() 

        f_print('检查数据库,是否存在下载文件......')
        # condition_element={ 'category_id':self.db_category_id,
                            # 'filename':self.db_filename}
        # #searchinfos=pga.search_db_table('file_info_db','file_info',condition_element)
        # searchinfos=pga.search_db_table(db_name,table_name,condition_element)            
        
        
        ####方案1，模糊匹配
        # search_name = '\'%s%s%s\''%('%',check_name,'%')
        # sqlcmd='SELECT * FROM %s WHERE category_id = %s and filename like %s'%(table_name,self.db_category_id,search_name)           
        
        
        ####方案2，
        search_name = check_name
        sqlcmd="SELECT * FROM %s WHERE category_id = %s and filename = '%s'"%(table_name,self.db_category_id,search_name)
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)
        
        
        #f_print(searchinfos)
        if(searchinfos):#数据库不为空
            searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
            category_id = searchinfo['category_id']
            category_abbr_en = searchinfo['category_abbr_en']
            filename = searchinfo['filename']
            state = searchinfo['state']
            
            ##state是字符串,不是BOOL类型
            f_print('state = %s' % state)
            #f_print('category_id = %s'%category_id)
            f_print('category_id = %s' % category_id)            
            f_print('category_abbr_en = %s' % category_abbr_en)
            f_print('filename = %s' % filename)
            #f_print('db_filename = %s'%self.db_filename)
            ####category_id比较多余的，因为查询数据库的时候，就是按category_id查询的
            #if(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='True'):  

            ####剔除日期是原始网站的文件名
            # ori='SABER_L2B_YYYYDOY_XXXXX_02.07.nc.gz'
            # rename='SABER_L2B_YYYYDOY_XXXXX_02.07_YYYYMMDD_hhmmss.nc.gz'
            # rename='_'.join(rename.split('_')[0:-2])
            # print(rename==ori[0:len(rename)])
            
            download_name = '_'.join(filename.split('_')[0:-2])
            #if (filename==self.db_filename) and (state=='True'):
            #if (download_name==check_name[0:len(download_name)]) and (state=='True'):             
            if (filename==check_name) and (state=='True'):            
                #print ('return 0')                
                return 0
                
            #elif(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='False'):                    
            #elif (filename==self.db_filename) and (state=='False'):
            #elif (download_name==check_name[0:len(download_name)]) and (state=='False'):              
            elif (filename==check_name) and (state=='False'):            
                #print ('return 1')
                return 1
                
            # elif (filename==self.db_filename) and (state=='True') and ():
                # print ('return 1')
                # return 1                
            ####这种情况不存在，因为查询的时候，是filename，category_id同时为查询条件
            # elif(category_id!=self.db_category_id) or (filename!=self.db_filename):
                # print ('return 2')
                # return 2
        else:
            #print ('return 2')
            return 2
            
            
            
            
    ##数据库更新
    def update_db(self,config_infos,condition_infos):
        #db_name     = 'yjy015'
        db_name = configs['db_name']        
        table_name  = 'data_file_info'    
        pga=PostgresArchive()
        ####此处写法bug，导致所有state=False的记录，都set成config_infos里的配置信息      
        pga.update_db_table(db_name,table_name,config_infos,condition_infos) 
        
        
        
    def record_monitor(self,log,status):
        """
        1. 下载数据监控表
        
        """
        table_name = 'data_monitor'
        task_name = '数据收集 ' + self.category_name_zh + ' ' + self.category_abbr_en
        
        
        ####数据库监控表入库
        ####如何更改调度任务表，调度任务表的信息用不用修改，我们最关心的是file_info数据表，调度任务表只是自动调度任务，最终以file_info表收集的信息为主
        create_time = get_current_BJT()##入库时间按北京时间
        update_time = get_current_BJT()##入库更新时间按北京时间

        ##监控表参数设置
        exe_fullpath = configs['exe_fullpath']
        cmd = 'python3' + ' ' + exe_fullpath + ' ' + self.category_abbr_en + ' ' + self.starttime + ' ' + self.endtime        
        
        pga=PostgresArchive()
        config_infos={
                    'task_name':task_name,
                    'create_time':create_time,
                    'update_time':update_time,                
                    'log':log,
                    'status':status,
                    'cmd':cmd,
                    'data_class':self.data_class,
                    'research_area':self.research_area,
                    'website':self.website,
                    'category_abbr_en':self.category_abbr_en
                    }
                    
        #pga.insert_db_table(database_name='task_db', table_name='t_task_monitor', config_element = config_infos)
        #pga.insert_db_table(database_name='yjy015', table_name='task_monitor', config_element = config_infos)
        pga.insert_db_table(database_name=db_name, table_name=table_name, config_element = config_infos)    
    
    
    
    
    def record_data(self,check_name):
         
        ####入库之前增加检查是否存在此数据，存在就跳过还是更新，暂时跳过
        
        status_code = self.check_db(check_name)
        #print (type(status_code))
        #print ('数据库检查完毕，返回状态码 %d '% status_code)
        if(status_code==0x000):
            f_print('数据库中存在此数据，不需要入库！')
            return False
        elif(status_code==0x001):
            f_print('数据库中存在此数据，需要更新库！')
        # elif(status_code==0x002):
            # f_print('数据库中不存在此数据，需要插入库！')
            ##pass        
        elif(status_code==0x002):
            f_print('数据库为空 或者数据库中不存在此数据，需要插入库！')       
          
        #input()
        ####入库操作
        #print ('入库1......')

        self.db_filename=self.localfilename
        #self.db_path=self.db_path
        self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        #print ('localfullpath = %s'%localfullpath)
        #input()
        
        f_print('self.downloadfullpathname = %s'%self.downloadfullpathname)
        #input()
        self.db_file_size=os.path.getsize(self.downloadfullpathname)        
        #self.db_file_size=os.path.getsize(self.localfullpathname)
        #print ('self.db_file_size = %d'%self.db_file_size)
        #input()
        f_print('入库......')
        #input()
        
        if(status_code==0x002):
            f_print('status_code==0x002,插入库操作......')
        #if(status_code==0x002)or(status_code==0x003):
            self.db_state=True
            self.db_log='成功'
            self.record_db()
            #print("record_db finished!")
            
        if(status_code==0x001):
            f_print('status_code==0x001,更新库操作......')
            ##更新状态为False的数据库，更新为True
            config_infos={
                        'file_size':self.db_file_size,
                        'record_time':self.db_record_time,
                        'state':True,
                        'log':'成功'}
            ## 如果condition条件不满足，某些条件不匹配，导致更新失败
            ## db_record_time每次都不一样，所以需要更新，不能作为查询条件
            ## db_file_size如果下载失败，有可能是空，大小为0，不能作为查询条件
            ## db_log，失败的log种类很多，每次都不同，不能作为查询条件
            condition_infos={
                        #'category_id':self.db_category_id,
                        'category_abbr_en':self.db_category_abbr_en,                        
                        'filename':self.db_filename,
                        'path':self.db_path,
                        #'record_time':self.db_record_time,
                        'start_time':self.db_start_time,
                        'end_time':self.db_end_time,
                        #'file_size':self.db_file_size,
                        'state':self.db_state,
                        #'log':self.db_log,
                        'element_storage_status':self.db_element_storage_status}                          
            self.update_db(config_infos,condition_infos)           
            #print("update_db finished!")
            #input()
        return True
    
    
    ##写磁盘操作,并记录数据库
    def record_datas(self):
        """
        1. 根据最新正则表达式，无法确定下载文件名和数据库名，所以需要先下载再查询数据库
        2. 下载的时候默认本地存在，就不下载
        """
        #f_print('record_datas......')

        
        #写文件使用绝对路径，需要读取cfg配置文件，写数据库写相对路径
        #data_rootpath = configs['data_rootpath']
        #print(configs)
        #f_print('dataroot_path = %s'%dataroot_path)        
        #localpath = os.path.join(dataroot_path,self.db_path,localfilename)

        
        rootpath = configs['rootpath']
        #self.localfullpath       = data_rootpath + self.db_path
        self.localfullpath       = rootpath + '/' +  configs['dataname'] + '/' + self.save_path
        
        
        ####根据和前端的讨论，默认发布的根路径，data文件夹默认不清楚，所以数据库里需要写入此文件夹
        ####从根路径种截取data字符串
        
        # dir_path,dir_name = find_last_dir(data_rootpath)
        # self.db_path = '/' + dir_name + '/' + self.save_path
        
        self.db_path = '/' + configs['dataname'] + '/' + self.save_path

        
        ###存放数据的路径,需要根路径+相对路径
        if not os.path.exists(self.localfullpath):
            f_print('路径不存在，需要创建路径，%s'%self.localfullpath)
            #input()
            try:
                os.makedirs(self.localfullpath)
                f_print("makedir...... %s" % self.localfullpath)
            except Exception as e:
                raise Exception(traceback.format_exc())
                
        # try:             
            # print ('开始爬虫......')
            # print (fullurl)
            # #input()

            # print ('获取远程文件名......')
            #infos = wget.filename_fix_existing(fullurl) 
            #print (infos)
            #print ('file_name = %s'%file_name)
            #input()
            #file_name = wget.download(fullurl, out=localfullpath,timeout=20)  
            
            ####方案1，python第3方库wget
            ##-T,--timeout=SECONDS 设置超时时间 
            ##这里的timeout是wget下载过程中一次读取数据的超时时间，并不是整个下载任务的超时时间
            #file_name = wget.download(fullurl, out=localfullpath)
            #print('\n')
            
            
            ####方案2，linux命令wget
            ##-O,  --output-document=FILE    将文档写入 FILE
            ##-T,  --timeout=SECONDS         将所有超时设为 SECONDS 秒。
        f_print('开始爬虫......')
        f_print('网站全路径 %s'%self.full_url)
        f_print('本地下载路径 %s'%self.localfullpath)
        #cmd = 'wget -O %s %s'%(localfullpath,fullurl)
        
        
        #3分钟下载
        #cmd = 'wget --tries=3 -T 180 -O %s %s'%(localfullpath,fullurl)
        #cmd = 'wget --tries=3 -T 60 -O %s %s'%(localfullpath,fullurl)
        
        ####判断正则表达式
        if self.regular_expression == '':
            f_print('不需要正则表达式匹配......')
            self.localfullpathname   = self.localfullpath + '/' + self.localfilename
            f_print('写文件的全路径：%s' % self.localfullpathname)    
            cmd = 'wget --timestamping --tries=%d -T %d -O %s %s'%(1,60,self.localfullpathname,self.full_url)
        else:
            f_print('需要正则表达式匹配......')
            ##方案1，正则表达式，linux目前有些文件匹配不成功，windows下没有问题
            #cmd = 'wget -e robots=off --no-cookies --no-cache --no-directories --no-parent --timestamping -m -nH --tries=%d -T %d --directory-prefix=%s --accept-regex=%s %s'%(3,60,self.localfullpath,self.regular_expression,self.url)
            
            ##方案2，使用list，匹配很好
            cmd = 'wget -e robots=off --no-cookies --no-cache --no-directories --no-parent --timestamping -m -nH --tries=%d -T %d --directory-prefix=%s --accept %s %s'%(3,60,self.localfullpath,self.regular_expression,self.url)
                
        
        f_print (cmd)
        try:
            ##方案2
            ret = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=None)
            ##只有3个条件同时满足，才任务正常执行成功
            #if ret.returncode == 0 and ret.stderr == '' and ret.stdout == '':
            #if ret.returncode == 0 and ret.stderr == '':  

            ##不能根据返回值来判断数据下载正确与否，数据下载成功也出现returncode不等于0的情况
            # if ret.returncode == 0:
                # print ('ret.returncode = %s'%ret.returncode)
                # print ('ret.stderr = %s'% ret.stderr)   
                # #pass
                
            # ##方案3
            # # status = os.system(cmd)
            # # print ('status = %d'% status)
            # # if (status == 0):
                # # pass
                
            # ##命令执行成功，但是命令种有其它异常情况
            # else:
                # ####删除本地空文件
                # print ('ret.returncode = %s'%ret.returncode)
                # print ('ret.stderr = %s'% ret.stderr)                
                # try:
                    # print ('删除本地空文件 | %s' % self.localfullpathname)                   
                    # os.remove(self.localfullpathname)
                  
                # except Exception as e:
                    # #raise Exception(traceback.format_exc())             
                    # raise Exception(str(e)) 
                    
                    
                #print ('wget下载数据失败')
                #raise Exception(ret.stderr) 
        ####命令没有执行成功，有异常        
        except Exception as e:
            #print (cmd)
            raise Exception(traceback.format_exc())             
            #raise Exception(str(e)) 
        
        ####根据正则表达式判断是否需要入库
        if self.regular_expression == '':
            # check_name = self.download_filename ##不需要正则表达式匹配的，直接按下载名来和数据库里查询到的文件匹配
            # localfilename,suffix = os.path.splitext(download_filename)
            # self.localfilename   = localfilename + '_' + self.localfilename_timestamp + suffix
            
            self.downloadfullpathname=self.localfullpathname
            ####入库之前，判断下载的文件是否合法，大小是否正确
            if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname)!= 0:
                #pass
                self.record_monitor(log='成功',status='True')
            else:
                ##err = '%s %s %s'%(cmd,'下载数据失败,本地文件名',self.downloadfullpathname)                
                #err = '%s'%(cmd)
                #raise Exception(err)
                self.record_monitor(log='失败',status='False')
            

            ####没有正则匹配，直接按添加日期之后的文件名判断入库
            if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname)!= 0:             
                self.record_data(self.localfilename)
            ##文件下载完成,但是文件大小为0，需要删除空文件
            if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname) == 0:                 
                os.remove(self.downloadfullpathname)
                    
        else:
            ####需要正则表达式匹配的，需要遍历目录文件，否则不知道下载的文件名称
            for download_filename in os.listdir(self.localfullpath):
                f_print('')
                # if (download_filename == 'index.html'):
                    # continue
                
                ##剔除其它文件的判断
                if False == download_filename.endswith(self.suffix):
                    continue
                
                ####第1步，先判断遍历的文件里有没有入库的，如果有就跳过此文件，遍历的目的是本目录下载的文件名有入库的也有没入库的，需要判断 
                status_code = self.check_db(download_filename)
                if(status_code==0x000):
                    f_print('数据库中存在此数据，不需要修改下载目录下的文件名！')
                    continue
                elif(status_code==0x001):
                    f_print('数据库中存在此数据，需要更新库，不需要修改下载目录下的文件名！')
                    continue 
                # elif(status_code==0x002):
                    # f_print('数据库中不存在此数据，需要插入库！')
                    ##pass        
                elif(status_code==0x002):
                    f_print('数据库为空 或者数据库中不存在此数据，需要插入库，需要修改下载目录下的文件名！')    
                
                
                ####第2步，如果库里没有，添加日期，再去库里查找，入库
                # localfilename,suffix = os.path.splitext(download_filename)
                # self.localfilename   = localfilename + '_' + self.localfilename_timestamp + suffix            
                # #check_name = download_filename

                ##需要特殊处理*.nc.gz后缀名
                if '.nc.gz' in download_filename:
                    localfilename = download_filename.rstrip('.nc.gz')
                    suffix = '.nc.gz'
                else:
                    localfilename,suffix = os.path.splitext(download_filename)
                self.localfilename   = localfilename + '_' + self.localfilename_timestamp + suffix
                
                
                self.downloadfullpathname      = self.localfullpath + '/' + download_filename
                ####入库之前，判断下载的文件是否合法，大小是否正确
                if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname)!= 0:
                    #pass
                    self.record_monitor(log='成功',status='True')
                else:
                    ##err = '%s %s %s'%(cmd,'下载数据失败,本地文件名',self.downloadfullpathname)                
                    #err = '%s'%(cmd)
                    #raise Exception(err)
                    self.record_monitor(log='失败',status='False')
                
                
                self.localfullpathname   = self.localfullpath + '/' + self.localfilename
                #os.move(downloadfullpahname,self.localfullpathname)
                
                ##文件下载完成,但是文件大小不为0，需要入库
                if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname)!= 0:                
                    retcode = self.record_data( self.localfilename )
                
                    ####可能出现文件一直追加日期的bug,SABER_L2B_2020046_98620_02.07.nc_20200214_080000_20200214_080000.gz
                    ####修改文件名之前，先判断数据库中有没有，有的话就不修改文件名称
                    #if record_data == True:
                    ####如果加日期，都需要更改本地的文件名，不管retcode返回值是多少
                    ####如果数据库里有，继续修改本地文件名，会覆盖掉之前的文件
                    ####每次重新下载任务，本地没有下载文件，因为文件被重命名了
                    os.rename(self.downloadfullpathname,self.localfullpathname)
                    f_print('修改文件名 %s -> %s' % (self.downloadfullpathname,self.localfullpathname))
                
                ##文件下载完成,但是文件大小为0，需要删除空文件
                if os.path.exists(self.downloadfullpathname) and os.path.getsize(self.downloadfullpathname) == 0:                 
                    os.remove(self.downloadfullpathname)
                    
                ##其它情况,比如路径不存在,不需要处理
                
        return
    

    
    def download_wget(self,starttime, endtime):
        
        try:
            self.record_datas()
        except Exception as e:
            ##异常直接入库，报错信息写入数据库
            ##异常信息不入库，如果错误了，就录入到任务调度库，保证数据收集的库里的数据都是收集成功的记录
            #self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #self.db_log='%s'%traceback.format_exc()
            #self.record_db()
            raise Exception(traceback.format_exc())             
            #raise Exception(str(e)) 
        return 
    
    
    
    
    def start(self, starttime, endtime):
        ####从数据库里读取配置信息
        self.get_sql_info()
        
        
        self.starttime  = starttime          # 下载配置的开始时间
        self.endtime    = endtime            # 下载配置的结束时间
        
        
        #self.db_category_id = self.category_id##每种大类数据self.db_category_id不变
        
        # 循环时间,容易死循环，谨慎使用while
        #while starttime <= endtime:
        # print ('starttime = %s'%starttime)
        # print ('endtime = %s'%endtime)            
        yyyy = starttime[0:4]
        mm = starttime[4:6]
        dd = starttime[6:8]
        hh = starttime[8:10]
        yymm = starttime[2:6]   #1910,19年10月
        mmdd = starttime[4:8]   #1910,19年10月            
        yymmdd = starttime[2:8] #191022,19年10月22
        yyyymm = starttime[0:6]
        hhmmss=starttime[8:14]
        hhmm=starttime[8:12]
        yyyymmdd=starttime[0:8]
        yyyymmddhhmm=starttime[0:12]
        yyyymmddhhmmss=starttime
        DOY=self.get_DOY(int(yyyy),int(mm),int(dd))
        #print(yyyymmddhhmmss)
        
        
        ####换算开始，结束时间，入库时需要
        self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')


        ####第1步 替换归档路径
        self.save_path=self.save_path.replace('YYYYMMDD',str(yyyymmdd))             
        #self.save_path=self.save_path.replace('YYYYMM',str(yyyymm))
        self.save_path=self.save_path.replace('YYYYMM',str(yyyymm))
        #self.db_path = self.save_path
        #print (self.save_path)

        
        ####第2步 替换下载文件名
        #gps_tec15min_igs_YYYYMMDD_v01.cdf
        ####优先匹配复杂的，字符串多的
        self.download_filename=self.download_filename.replace('YYYYMMDD',str(yyyymmdd))
        self.download_filename=self.download_filename.replace('YYYYMM',str(yyyymm))
        self.download_filename=self.download_filename.replace('YYYY',str(yyyy))             
        self.download_filename=self.download_filename.replace('DOY',str(DOY))             
        self.download_filename=self.download_filename.replace('hhmmss',str(hhmmss))               
        self.download_filename=self.download_filename.replace('hhmm',str(hhmm))   
        self.download_filename=self.download_filename.replace('YYMM',str(yymm))              
        self.download_filename=self.download_filename.replace('MM',str(mm))  
        self.download_filename=self.download_filename.replace('DD',str(dd))              
        
        ####第3步 替换归档文件名
        ####因为调度里加了容错处理，可能启动任务的时刻不是整点，整点多1-2秒的误差，导致文件命名的时候也会多1-2秒，需要特殊处理成整点时刻的文件名
        year    = datetime.datetime.strptime(self.endtime, "%Y%m%d%H%M%S").year
        month   = datetime.datetime.strptime(self.endtime, "%Y%m%d%H%M%S").month
        day     = datetime.datetime.strptime(self.endtime, "%Y%m%d%H%M%S").day
        hour    = datetime.datetime.strptime(self.endtime, "%Y%m%d%H%M%S").hour
        minute  = datetime.datetime.strptime(self.endtime, "%Y%m%d%H%M%S").minute
        second  = 0
        self.localfilename_timestamp=(datetime.datetime(year,month,day,hour,minute,second)).strftime('%Y%m%d_%H%M%S')          
        
        #self.localfilename_timestamp=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y%m%d_%H%M%S')
        
        ##需要特殊处理*.nc.gz后缀名
        if '.nc.gz' in self.download_filename:
            localfilename = self.download_filename.rstrip('.nc.gz')
            suffix = '.nc.gz'
        else:
            localfilename,suffix = os.path.splitext(self.download_filename)
        self.localfilename   = localfilename + '_' + self.localfilename_timestamp + suffix
        
        
        ####第4步 替换url网页链接
        ####self.url不能替换，for循环替换全局变量，导致下一次for循环找不到DOY字符串
        
        ####根据当前的数据库配置的默认mids11字符串，计算需要下载的数据所属的midsxx
        midsxx=self.get_midssxx('mids11',str(yyyy))
        self.url=self.url.replace('mids11',str(midsxx))    
        self.url=self.url.replace('DOY',str(DOY))                   #replace替换完，需要赋值，否则exp的内容没有更改
        self.url=self.url.replace('YYYYMMDD',str(yyyymmdd))         #replace替换完，需要赋值，否则exp的内容没有更改
        self.url=self.url.replace('YYYYMM',str(yyyymm))             #replace替换完，需要赋值，否则exp的内容没有更改
        self.url=self.url.replace('YYYY',str(yyyy))                 #replace替换完，需要赋值，否则exp的内容没有更改            
        self.url=self.url.replace('MM',str(mm))                     #replace替换完，需要赋值，否则exp的内容没有更改
        self.url=self.url.replace('DD',str(dd))                     #replace替换完，需要赋值，否则exp的内容没有更改             
        #print('url = %s'%url)                                
        self.full_url = self.url + '/' + self.download_filename
        f_print('网站全路径 %s' % self.full_url )
        #input()
        
        
        ####第5步 替换正则表达式日期
        regular_expression = self.regular_expression ##需要特殊处理的正则表达式，需要定义正则表达式初始值
        
        ####优先匹配复杂的，字符串多的
        self.regular_expression=self.regular_expression.replace('YYYYMMDD',str(yyyymmdd))
        self.regular_expression=self.regular_expression.replace('YYYY',str(yyyy))            
        self.regular_expression=self.regular_expression.replace('DOY',str(DOY))              
        self.regular_expression=self.regular_expression.replace('hhmmss',str(hhmmss))               
        self.regular_expression=self.regular_expression.replace('hhmm',str(hhmm))
        self.regular_expression=self.regular_expression.replace('YYMM',str(yymm))
        self.regular_expression=self.regular_expression.replace('MMDD',str(mmdd)) 
        self.regular_expression=self.regular_expression.replace('MM',str(mm)) 
        self.regular_expression=self.regular_expression.replace('DD',str(dd))              
        self.regular_expression=self.regular_expression.replace('hh',str(hh))
        
        ####第143种数据类型，需要特殊处理，20200527，2020527，月份有可能少1位，YYYYMMDD_*_NL*.jpg
        if 'SWPC_synoptic_maps'== self.category_abbr_en:
            f_print('进入正则匹配特殊处理，处理数据类型 %s'%self.category_abbr_en)
            #print (mm)
            #input()
            if mm[0] == '0':##月份01-09
                #print (mm)
                regular_expression=regular_expression.replace('YYYY',str(yyyy))
                regular_expression=regular_expression.replace('MM',str(mm[1]))
                regular_expression=regular_expression.replace('DD',str(dd))
                self.regular_expression = self.regular_expression + ',' + regular_expression ##正则匹配列表
            
        f_print('正则表达式规则 %s' % self.regular_expression)
        #input()
        
        
        ####存放数据的路径,需要根路径+相对路径
        try:
            self.download_wget(starttime, endtime)
        except Exception as e:
            #raise Exception(e)
            raise Exception(traceback.format_exc()) 
        
        
        ####特殊情况占大多数
        #yyyymmddhhmmss = (datetime.datetime.strptime(starttime, "%Y%m%d%H%M%S") + datetime.timedelta(days=1)).strftime("%Y%m%d%H%M%S")
        #starttime=yyyymmddhhmmss####日期自动加1，更新开始时间
        
        return

