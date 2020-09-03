__author__ = "fengyuqiang"
# -*- coding: utf-8 -*-




"""
@modify
2020-05-06 15:21:43
                    1. ftp, connect的时候, url需要去掉ftp://字符串
                    
2020-05-08 14:59:10
                    1. 写文件，使用绝对路径，需要从cfg配置文件里读取绝对路径的根路径
                    2. 入库，只需要入相对路径即可，UI界面，在tomcat里配置绝对路径的根路径                    


"""





import os
import ftplib
import socket
import requests
import re
import xml.etree.ElementTree as ET
import datetime
import traceback


from logger.logger import *
#from file_info.daily_download_datatypes import *
from db.postgres_archive import *
from cfg.conf import *



class FtpDownload():
    #初始化并连接ftp,datatype拼写错误datetype
    def __init__(self,datatype,searchinfo):
        self.datatype = datatype        #下载数据类型
        self.searchinfo = searchinfo
        self.category_id=0              # 数据库查询到的id
        self.url = ''                   #下载地址
        self.band = ''                  #数据波段
        self.exp = ''                   #正则表达式
        self.savepath = ''              #保存路径
        self.starttime = ''             # 开始时间
        self.endtime = ''               # 结束时间
        self.username= ''               #账户
        self.passwd = ''                #密码
        self.port = 21                  #端口
        self.cwd = ''                   #目录
        self.ftp=None                   #初始化ftp返回
        
        ####归档入库的所有全局变量定义，加db前缀
        ####如果数据下载失败，使用此全局变量入库
        self.db_category_id=0
        self.db_filename=''
        self.db_path=''
        self.db_record_time=''
        self.db_start_time=''
        self.db_end_time=''
        self.db_file_size=0
        self.db_state=False
        self.db_log=''                      ####全局变量，可以在程序中使用此变量，记录实际的错误信息
        self.db_element_storage_status=False####全局变量，要素提取入库成功之后，需要更新状态为True
        
    

    def get_DOY(self,year,month,day):
        import calendar
        months=[0,31,59,90,120,151,181,212,243,273,304,334]#每个月对应的天数
        if 0<month<=12:
            DOY=months[month-1]
        else:
            print ('month error.')
        DOY+=day
        leap=0
        #判断平年闰年
        check_year=calendar.isleap(year)
        if check_year == True:
            DOY+=1           
        return DOY

        
    ####url会被修改掉，需要传入修改后的url，否则for循环导致url有bug
    def ftpconnect(self,url):
        ##增加连接报错，异常处理
        try:
            #ftp = ftplib.FTP(self.url)
            #ftp = ftplib.FTP(url)
            self.ftp = ftplib.FTP()
        #except (socket.error, socket.gaierror):
        except Exception as e:
            #print('[ERROR]: could not reach %s %s' % (self.url,str(e)))
            print('[ERROR]: could not reach %s %s' % (url,str(e)))
            #return None
            raise Exception (e)
        print('ftp网络正常......')
        
        try:
            #ftp.connect(self.url, self.port)
            self.ftp.connect(url, self.port)
        except Exception as e:
            print('[ERROR]: could not connect %s' % str(e))
            #return None
            raise Exception (e)            
        print('ftp连接正常...')
        
        ####
        self.ftp.set_pasv(False)  # 如果被动模式由于某种原因失败，请尝试使用活动模式。

        ##增加登录判断，异常直接返回错误信息
        try:
            self.ftp.login(self.username,self.passwd)
        except (ftplib.error_perm):
            print('[ERROR]: could not login anonymously')
            ftp.quit()  # 需要退出，否则下次连接，提示有2个连接
            #return None
            raise Exception (e)            
        print('ftp登录正常...')
        #print(ftp.dir())
        #return self.ftp
    
    
    def get_sql_info(self):
        print ('into get_sql_info......')
        #self.url = self.searchinfo['url'][]
        self.url = self.searchinfo['url'][6:]        
        self.band = self.searchinfo['band']
        self.cwd = self.searchinfo['cwd']
        self.exp = self.searchinfo['exp']
        self.savepath = self.searchinfo['savepath']
        self.category_id = self.searchinfo['category_id']   
        #self.port=21##默认值   
        print (self.url)
        print (self.band)        
        print (self.cwd)
        print (self.exp)
        print (self.savepath)
        print (self.category_id)        
        return
        
      
    ##连接5次，5次不成功就退出，报错
    def request_get(self,url,max=5):
        user_agent='wswp'
        headers={'User_Agent': user_agent}
        proxies=None
        for m in range(max):
            req = requests.get(url, headers=headers, proxies=proxies)  ##由于顶层函数调用此函数，加try,所以异常直接报错，不进行pr
            #req = requests.get(url, verify=False)##由于顶层函数调用此函数，加try,所以异常直接报错，不进行print下面的操作
            ##如果返回404，可以重复进入死循环
            print(req.status_code)
            if (404 == req.status_code):
                time.sleep(2)#连接太快，网页会被ban掉
                continue
            elif (200 == req.status_code):
                return req
        return req
        
        
    def gethtml(self,url):
        #req = requests.get(url, verify=False)
        req = self.request_get(url)
        print(req)
        if(req==None):
            logg=Log()
            logg.append_log('%s%s%s%s'%(self.url,self.datatype,self.band,' failed to download.'))
            exit(1)
        #print(req.status_code)
        html = req.text  # 获取网页源码
        return html       
        
    
    ##数据入库
    def record_db(self):
        print ('into record_db......')    
        pga=PostgresArchive()
        config_infos={
                    'category_id':self.db_category_id,
                    'filename':self.db_filename,
                    'path':self.db_path,
                    'record_time':self.db_record_time,
                    'start_time':self.db_start_time,
                    'end_time':self.db_end_time,
                    'file_size':self.db_file_size,
                    'state':self.db_state,
                    'log':self.db_log,
                    'element_storage_status':self.db_element_storage_status}                   
        pga.insert_db_table('file_info_db','file_info',config_infos)
    
    
    ##数据库更新
    def update_db(self,config_infos,condition_infos):
        print ('into update_db......')        
        pga=PostgresArchive()
        ####此处写法bug，导致所有state=False的记录，都set成config_infos里的配置信息
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
        pga.update_db_table('file_info_db','file_info',config_infos,condition_infos)    

        
    ##核对数据库里是否存在此数据，
    ##category_id,filename相同，就是同1个数据;或者数据库为空和2个条件不全满足的可以入库 
    ##返回状态码：
    #000代表数据库中存在不需要入库
    #001代表数据库中存在此数据，但是state=FALSE，代表没有下载成功，需要update数据库，并把数据下载到磁盘上
    #002代表数据库不为空，但是数据库中不存在此数据，需要insert此数据
    #003代表数据库为空，需要insert此数据
    def check_db(self,filename):
        print ('into check_db......')
        self.db_filename=filename
        
        pga=PostgresArchive()
        condition_element={
                    'category_id':self.db_category_id,
                    'filename':self.db_filename}
        searchinfos=pga.search_db_table('file_info_db','file_info',condition_element)
        print (searchinfos)
        
        if(searchinfos):#数据库不为空
            searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
            category_id = searchinfo['category_id']
            filename = searchinfo['filename']
            state = searchinfo['state']
            if(category_id==self.db_category_id) and (filename==self.db_filename) and (state==True):
                return 0x000
            elif(category_id==self.db_category_id) and (filename==self.db_filename) and (state==False):
                return 0x001
            elif(category_id!=self.db_category_id) or (filename!=self.db_filename):
                return 0x002
        else:
            return 0x003

            
    def record_data(self,path,url,cwd,band,starttime):
        print ('into record_data......')                      
        bufsize = 1024
        bands = list(band.split(","))      
        print('bands = %s' % bands)
        for band in bands:
            #file_remotename = starttime + band
            file_remotename = band
            ####ftp全局变量类
            #self.ftp = self.ftpconnect(self.url)
            #self.ftp = self.ftpconnect(url)
            self.ftpconnect(url)                        
            print (self.ftp)
            
            if(self.ftp==None):
                print('ftp连接失败')   
                ####记录数据库
                self.db_filename=file_remotename
                self.db_path=path
                self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.db_log = 'ftp连接失败'
                self.record_db()#暂时这么处理，数据库里，如果重复下载一种数据的固定日期的数据，可能会有很多重复的
                
                ####记录到本地日志文件里
                #logg=Log()
                debug_log('%s%s%s%s%s'%(url,cwd,self.datatype,band,' failed to download.'))
                ##异常直接退出，物理要素提取直接跳过
                exit(1)
            
            ####下载之前，先判断ftp服务器有无此文件，没有直接入库错误信息，并break或者continue
            print (self.getfilelist(cwd))
            if file_remotename not in self.getfilelist(cwd):
                ####入库失败信息，并返回或者break，或者continue
                self.db_filename=file_remotename
                self.db_path=path
                self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log = 'ftp服务器上,文件不存在.'
                self.record_db()
                continue
            
            print ('self.datatype = %s'%self.datatype)
            if self.datatype in ftp_stage3_datatype1:
                print ('ftp_stage3_datatype1......')
                pat=starttime[2:6]+'.*'
                newpat=starttime[0:8]+ '_' + starttime[9:15] + '.tab'
                file_localname=re.sub(pat,newpat,file_remotename)
            if self.datatype in ftp_stage3_datatype2:
                #替换后缀，增加日期
                filestr,suffix=os.path.splitext(file_remotename)
                pat=suffix
                newpat='_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
                file_localname=re.sub(pat,newpat,file_remotename)
            if self.datatype in ftp_stage3_datatype3:
                #日期和数据类型互换位置
                filestr,suffix=os.path.splitext(file_remotename)#splitext分割后缀名，带.xxx
                name=re.findall(r'\D+',filestr)#除数字之外的字符串
                file_localname= name + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            if self.datatype in ftp_stage3_datatype4:
                #把html后缀名更改成txt,并在后缀名前,添加YYYYMMDD_hhmmss
                filestr,suffix=os.path.splitext(file_remotename)
                newsuffix=suffix.replace('html','txt')
                file_localname=filestr + '_' + starttime[0:8]+ '_' + starttime[8:14] + newsuffix
            if self.datatype in ftp_stage3_datatype5:
                #日期和数据类型互换位置
                filestr,suffix=os.path.splitext(file_remotename)#splitext分割后缀名，带.xxx
                splitstr = filestr.split('_')
                spitstr.pop(0)#剔除时间，pop(index)代表剔除的list里index位置的元素
                name = '_'.join(splitstr)
                file_localname= name + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            if self.datatype in ftp_stage3_datatype6:
                #日期和数据类型互换位置
                filestr,suffix=os.path.splitext(file_remotename)#splitext分割后缀名，带.xxx
                splitstr = filestr.split('_')
                spitstr.pop(-1)#剔除时间，pop(index)代表剔除的list里index位置的元素
                name = '_'.join(splitstr)
                file_localname= name + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            if self.datatype in ftp_stage3_datatype7:
                #日期和数据类型互换位置
                filestr,suffix=os.path.splitext(file_remotename)#splitext分割后缀名，带.xxx
                splitstr = filestr.split('_')
                name=spitstr.pop(-1)#剔除时间，然后把剔除的物理量赋值给name, pop(index)代表剔除的list里index位置的元素
                file_localname= name + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
                               
            if self.datatype in ftp_stage3_datatype8:
                filestr,suffix=os.path.splitext(file_remotename)#splitext分割后缀名，带.xxx
                splitstr = filestr.split('_')
                name=spitstr[0]
                file_localname= name + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            
            ####入库之前增加检查是否存在此数据，存在就跳过还是更新，暂时跳过
            status_code = self.check_db(file_localname)
            if(status_code==0x000):
                print ('status_code = %d ,数据库中存在此数据，不需要入库！' % status_code)
                return
            elif(status_code==0x001):
                print ('status_code = %d ,数据库中存在此数据，需要更新库！' % status_code)
            elif(status_code==0x002):
                print ('status_code = %d ,数据库中不存在此数据，需要插入库！' % status_code)
                #pass        
            elif(status_code==0x003):
                print ('status_code = %d ,数据库为空，需要插入库！' % status_code)
                

            print (file_localname)
            #file_localpath = os.path.join(path, file_localname)
            #写文件使用绝对路径，需要读取cfg配置文件，写数据库写相对路径
            dataroot_path = configs['dataroot_path']
            #file_localpath = os.path.join(dataroot_path,path,file_localname)    
            file_localpath = dataroot_path + path
            file_localfullpath=file_localpath + file_localname
            ###存放数据的路径,需要根路径+相对路径
            #print (self.db_path)
            if not os.path.exists(file_localpath):
                os.makedirs(file_localpath)
                print("makedir...... %s" % file_localpath)
            
            try:
                file_handle = open(file_localfullpath, 'wb').write
            except Exception as e:
                #raise Exception(str(e))
                raise Exception(traceback.format_exc())     
            
            self.ftp.cwd(cwd)
            self.ftp.retrbinary('RETR %s' % file_remotename, file_handle, bufsize)
            print ('Download %s -> %s'%(file_remotename,file_localfullpath))
            #print("Download %s Complete" % file_localfullpath)
            print("Download %s Complete")

            
            ####入库
            self.db_filename=file_localname
            self.db_path=path
            self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
            self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
            self.db_file_size=os.path.getsize(file_localfullpath)
            # self.db_state=True
            # self.db_log='成功'
            
            if(status_code==0x002)or(status_code==0x003):
                self.db_state=True
                self.db_log='成功'            
                self.record_db()
                print("record_db finished!")
            if(status_code==0x001):
            
                # ##更新状态为False的数据库
                # condition_infos={'state':False}
                # self.update_db(condition_infos)
                # print("update_db finished!")                
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
                            'category_id':self.db_category_id,
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
                print("update_db finished!")
                #input()                
        return
        
      
    def getfilelist(self,cwd):
        print ('into getfilelist......')
        self.ftp.cwd(cwd)
        print('ftp.nlst = %s' % self.ftp.nlst())
        return self.ftp.nlst()
    


    def get_midssxx(self,midsxx,yyyy):
        # mids=name=re.findall(r'\D+',midsxx)[0]  ##查找到的是list，需要转换成str
        # index=name=re.findall(r'\d+',midsxx)[0] ##查找到的是list，需要转换成str    
        mids=re.findall(r'\D+',midsxx)[0]  ##查找到的是list，需要转换成str
        index=re.findall(r'\d+',midsxx)[0] ##查找到的是list，需要转换成str
        ##以2019年为基准，进行加减运算
        sub = int(yyyy) - int(2019)
        #print (sub)
        index_s = str(int(index) + sub).zfill(2)
        #print (index_s)
        midsxx_s = mids + index_s
        #print (midsxx_s)
        return midsxx_s    

        
    def download_file(self,starttime,endtime):
        ####根据数据库查询信息，映射变量
        self.get_sql_info()
        self.starttime = starttime              ## 下载配置的开始时间
        self.endtime = endtime                  ## 下载配置的结束时间
        self.db_category_id = self.category_id  ## 每种大类数据self.db_category_id不变
        
        ##先处理字符串，再连接ftp
        yyyymmddhhmmss = starttime
        yyyymmddhhmm = starttime[0:12]
        yyyymmdd = starttime[0:8]
        yyyymm = starttime[0:6]
        yyyy = starttime[0:4]
        yymm = starttime[2:6]##201910,1910
        mmdd = starttime[4:8]##20191025，1025
        mm = starttime[4:6]
        dd = starttime[6:8]
        hhmmss = starttime[8:14]
        hhmm = starttime[8:12]
        print ('self.datatype = %s'%self.datatype)
        print ('self.starttime = %s'%starttime)       
        print ('self.endtime = %s'%endtime)       
        print(yyyymmddhhmmss)         
        
        ###ftp全局变量类
        # self.ftp = self.ftpconnect(self.url)
        # if(self.ftp==None):
            # print('ftp连接失败')  
            # logg=Log()
            # logg.append_log('%s%s%s%s%s'%(self.url,self.cwd,self.datatype,self.band,' failed to download.'))
            # exit(1)
        
        while starttime <= endtime:
            ####换算开始，结束时间，入库时需要
            self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
            self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')

            ####修改路径db_path
            #path=self.savepath.replace('YYYYMMDD',str(yyyymmdd))
            ####替换3次
            self.savepath=self.savepath.replace('YYYY',str(yyyy)) 
            self.savepath=self.savepath.replace('MM',str(mm)) 
            path=self.savepath.replace('DD',str(dd)) 
            
            # print (path)
            # if not os.path.exists(path):
                # os.makedirs(path)
                # print("makedir %s" % path)
                
            ####日期格式，比如20190805，只取到1908
            if self.datatype in ftp_stage1_datatype1:
                band=self.band.replace('YYMM',str(yymm))
                self.record_data(path,self.url,self.cwd,band,starttime)
            
            ####直接拼接
            if self.datatype in ftp_stage1_datatype2:
                print ('into ftp_stage1_datatype2...')
                self.record_data(path,self.url,self.cwd,self.band,starttime)            
            
            ####cwd,band替换时间
            if self.datatype in ftp_stage1_datatype3:
                cwd=self.cwd.replace('YYYYMMDD',str(yyyymmdd))
                cwd=cwd.replace('YYYYMM',str(yyyymm))
                band=self.band.replace('YYYYMMDDhhmmss',str(yyyymmddhhmmss))
                self.record_data(path,self.url,cwd,band,starttime)             
                print ('band = %s'%band)
                print ('cwd = %s'%cwd)
            
            ####
            if self.datatype in ftp_stage1_datatype4:
                band=self.band.replace('MMDD',str(mmdd))
                self.record_data(path,self.url,self.cwd,band,starttime)             
                print ('band = %s'%band)
            ####
            if self.datatype in ftp_stage1_datatype5:
                band=self.band.replace('MMDD',str(mmdd))
                band=band.replace('hhmm',str(hhmm))
                self.record_data(path,self.url,self.cwd,band,starttime)             
                print ('band = %s'%band)

            if self.datatype in ftp_stage1_datatype6:
                band=self.band.replace('YYYYMMDD',str(yyyymmdd))
                self.record_data(path,self.url,self.cwd,band,starttime)             
                print ('band = %s'%band)

            if self.datatype in ftp_stage1_datatype7:
                band=self.band.replace('YYYYMMDD',str(yyyymmdd))
                band=band.replace('hhmmss',str(hhmmss))
                self.record_data(path,self.url,self.cwd,band,starttime)             
                print ('band = %s'%band)                
            ####替换DOY和YYYYMMDDhhmm,下载YYYYMMDDhhmm需要和网站上的时间匹配
            ####1. 目前没有实现根据最近时间匹配，而是根据具体传入的时间来匹配，有可能匹配不到
            ####2. 因为2020年，网址链接自动加1，2019年是mids11，需要根据最近年份增加匹配替换规则
            if self.datatype in ftp_stage1_datatype8:
                DOY=self.get_DOY(int(yyyy),int(mm),int(dd))
                ####self.url不能替换，for循环替换全局变量，导致下一次for循环找不到DOY字符
                self.cwd=self.cwd.replace('YYYY',str(yyyy))
                self.cwd=self.cwd.replace('DOY',str(DOY))
                ####根据当前的mids11字符串，计算需要下载的数据所属的midsxx
                midsxx=self.get_midssxx('mids11',str(yyyy))
                cwd=self.cwd.replace('mids11',str(midsxx))              
                print('cwd = %s'%cwd)                    
                band=self.band.replace('YYYYMMDDhhmm',str(yyyymmddhhmm))
                print('band = %s'%band)
                self.record_data(path,self.url,cwd,band,starttime)
            
            ##时间递增1天
            starttime = (datetime.datetime.strptime(starttime, "%Y%m%d%H%M%S") + datetime.timedelta(days=1)).strftime("%Y%m%d%H%M%S")
            
        ##结束，关闭ftp
        self.ftp.close()
        
   