__author__ = "fengyuqiang"
# -*- coding: utf-8 -*-


"""
@modify history
2020-05-06 11:26:26 
                    1. 修改http_stage3_datatype1类型里localfilename，截取日期的bug
                    
                    
2020-05-08 14:59:10
                    1. 写文件，使用绝对路径，需要从cfg配置文件里读取绝对路径的根路径
                    2. 入库，只需要入相对路径即可，UI界面，在tomcat里配置绝对路径的根路径
                    
                    
"""


import os
import xml.etree.ElementTree as ET
import requests
import re
import traceback
import datetime
import time


from logger.logger import *
from urllib.request import urlopen
from bs4 import BeautifulSoup
from lxml import etree
from db.postgres_table import *
from db.postgres_archive import *
#from file_info.daily_download_datatypes import *
from cfg.conf import *




class HttpDownload:
    # 初始化
    def __init__(self,datatype,searchinfo):
        self.datatype = datatype    # 下载数据类型
        self.searchinfo=searchinfo  # 数据库查询信息
        self.category_id=0          # 数据库查询到的id
        self.url = ''               # 下载地址
        self.band = ''              # 数据波段
        self.exp = ''               # 正则表达式
        self.savepath = ''          # 保存路径
        self.starttime = ''         # 下载配置的开始时间
        self.endtime = ''           # 下载配置的结束时间
   
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
        self.db_log='失败'                          ####全局变量，可以在程序中使用此变量，记录实际的错误信息
        self.db_element_storage_status=False        ####全局变量，要素提取入库成功之后，需要更新状态为True
        
        
    
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
    
    
    ##数据库dict里获取各个字段的信息
    def get_sql_info(self):
        self.url = self.searchinfo['url']
        self.band = self.searchinfo['band']
        self.exp = self.searchinfo['exp']
        self.savepath = self.searchinfo['savepath']  
        self.category_id = self.searchinfo['category_id']      
        return
    
    
    ##连接5次，5次不成功就退出，报错
    def request_get(self,url,max=5):
        print ('into request_get...')
        user_agent='wswp'
        headers={'User_Agent': user_agent}
        proxies=None
        for m in range(max):
            try:
                req = requests.get(url, headers=headers, proxies=proxies)       ##由于顶层函数调用此函数，加try,所以异常直接报错，不进行pr
                #req = requests.get(url, verify=False)##由于顶层函数调用此函数，加try,所以异常直接报错，不进行print下面的操作
                ##如果返回404，可以重复进入死循环
                print(req.status_code)
                if (404 == req.status_code):
                    time.sleep(1)#连接太快，网页会被ban掉
                    continue
                elif (200 == req.status_code):
                    return req,req.status_code
            except Exception as e:
                #self.db_log='%s'%e
                raise Exception (e)
        #print (req)
        return req,req.status_code
    
    
    def gethtml(self,url):
        print ('into gethtml...')
        try:
            req,req.status_code = self.request_get(url)
        except Exception as e:
            raise Exception (e)            
        print(req)
        print(req.status_code) 
        # if(req==None):
            # logg=Log()
            # logg.append_log('%s%s%s%s'%(self.url,self.datatype,self.band,' failed to download.'))
            ####不能退出exit，否则 
            ####exit(1)
            # return None
        html = req.text  # 获取网页源码
        #print (html)
        return html,req.status_code
    
    
    def getfullURL(self,url,imglist):
        print ('into getfullURL...')
        imagURL = url + '/' + imglist
        print ('imagURL = %s'%imagURL)
        r,r.status_code = self.request_get(imagURL)
        print (r)
        return r,r.status_code
        
        
    ##数据入库
    def record_db(self):
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
    
    
    ##核对数据库里是否存在此数据，
    ##category_id,filename相同，就是同1个数据;或者数据库为空和2个条件不全满足的可以入库 
    def check_db(self,filename):
        print ('check_db......')
        self.db_filename=filename
        
        pga=PostgresArchive() 
        if self.datatype in http_stage4_datatype1:
            ####转换成datetime
            SUTC=datetime.datetime.strptime(self.db_start_time,"%Y-%m-%d %H:%M:%S").replace(hour=0,minute=0,second=0)
            EUTC=datetime.datetime.strptime(self.db_end_time,"%Y-%m-%d %H:%M:%S").replace(hour=23,minute=59,second=59)
                        
            ####datetime转换成string
            ####字符串添加单引号2019-06-16 00:12:00变成'2019-06-16 00:12:00'
            ####格式化输出\'\'，转义字符\
            SUTC_str='\'%s\''%SUTC.strftime("%Y-%m-%d %H:%M:%S")
            EUTC_str='\'%s\''%EUTC.strftime("%Y-%m-%d %H:%M:%S")
            splits = filename.split('_')
            XXXXX=splits[2]##编号
            XXXXX_str = '\'%s%s%s\''%('%',XXXXX,'%')
            ####查询当天下载入库的数据里，有没有filename
            sqlcmd='SELECT * FROM file_info WHERE category_id = %s and start_time BETWEEN %s and %s and filename like %s'%(self.db_category_id,SUTC_str,EUTC_str,XXXXX_str)
            searchinfos=pga.search_db_table_usercmd('file_info_db',sqlcmd)
            if(searchinfos):#数据库不为空
                searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
                state = searchinfo['state']
                ###名称不一样，只需要看XXXXX是否一样，filename==self.db_filename
                if (state=='True'):
                    print ('return 0')
                    return 0
                elif (state=='True'):
                    print ('return 1')
                    return 1                   
            else:
                print ('return 2')
                return 2
                
        else:
            condition_element={ 'category_id':self.db_category_id,
                                'filename':self.db_filename}
            searchinfos=pga.search_db_table('file_info_db','file_info',condition_element)

            print (searchinfos)
            if(searchinfos):#数据库不为空
                searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
                category_id = searchinfo['category_id']
                filename = searchinfo['filename']
                state = searchinfo['state']
                
                ##state是字符串,不是BOOL类型
                print ('state = %s'%state)
                print ('category_id = %s'%category_id)
                print ('db_category_id = %s'%self.db_category_id)
                print ('filename = %s'%filename)
                print ('db_filename = %s'%self.db_filename)
                ####category_id比较多余的，因为查询数据库的时候，就是按category_id查询的
                #if(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='True'):                
                if (filename==self.db_filename) and (state=='True'):
                    print ('return 0')
                    return 0
                #elif(category_id==self.db_category_id) and (filename==self.db_filename) and (state=='False'):                    
                elif (filename==self.db_filename) and (state=='False'):
                    print ('return 1')
                    return 1
                ####这种情况不存在，因为查询的时候，是filename，category_id同时为查询条件
                # elif(category_id!=self.db_category_id) or (filename!=self.db_filename):
                    # print ('return 2')
                    # return 2
            else:
                print ('return 2')
                return 2

              
    ##数据库更新
    def update_db(self,config_infos,condition_infos):
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

        
    ##写磁盘操作,并记录数据库
    def record_data(self,r,localfilename,starttime):
        print ('record_data......')
        
        ####全局变量使用有风险
        print ('localfilename = %s'%localfilename)
        filepath,filename =os.path.split(localfilename)
        print ('filename = %s'%filename)
        
        if self.datatype in http_stage3_datatype1:
            suffix='.nc.gz'
            splits = filename.split('_')
            XXXXX=splits[3]##编号
            localfilename = splits[0] + '_' + splits[1] + '_' + XXXXX + '_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            print ('localfilename = %s'%localfilename)
            #pass
            #pat=starttime[0:4]+'.*'
            #newpat=starttime[0:8]+ '_' + starttime[9:15] + '.nc.gz'
            #localfilename=re.sub(pat,newpat,filename)
        if self.datatype in http_stage3_datatype2:
            #pass
            filestr,suffix=os.path.splitext(filename)
            pat=starttime[0:8]+'.*'
            #newpat=starttime[0:8]+ '_' + starttime[8:14] + '.cdf'
            #newpat=starttime[0:8]+ '_' + starttime[8:14] + '.' + suffix
            newpat=starttime[0:8]+ '_' + starttime[8:14] + suffix
            localfilename=re.sub(pat,newpat,filename)
        if self.datatype in http_stage3_datatype3:
            #print ('http_stage3_datatype3...')
            #替换后缀，增加日期
            filestr,suffix=os.path.splitext(filename)
            pat=suffix
            newpat='_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            localfilename=re.sub(pat,newpat,filename)
        if self.datatype in http_stage3_datatype4:
            #替换后缀，增加日期

            splitstr,suffix = filename.split('.')
            #splitstr,suffix = os.path.splittext(filename)
            splitstrs=splitstr.split('_')
            YYYYMMDD=splitstrs[0]
            hhmm=splitstrs[1]
            ss='00'#没有秒信息，需要补00
            datatype=splitstrs[-1]
            filename=datatype + '_' + YYYYMMDD + '_' + hhmm +  ss + '.' + suffix
            localfilename=filename
            
        if self.datatype in http_stage3_datatype5:
            filestr,suffix=os.path.splitext(filename)
            pat=starttime[2:6]+'.*'                                     ##201910,截取1910
            newpat='_' + starttime[0:8]+ '_' + starttime[8:14] + suffix
            print (filename)
            print (pat)
            print (newpat)
            localfilename=re.sub(pat,newpat,filename)
            
        if self.datatype in http_stage3_datatype6:
            #filestr,suffix=os.path.splitext(filename)
            pat='V2.0'
            newpat=starttime[0:8]+ '_' + starttime[8:14]
            print (filename)
            print (pat)
            print (newpat)
            localfilename=re.sub(pat,newpat,filename)            
        if self.datatype in http_stage3_datatype7:
            #替换后缀，增加日期
            splitstr,suffix = filename.split('.')
            #splitstr,suffix = os.path.splittext(filename)
            splitstrs=splitstr.split('_')
            YYYYMMDD=splitstrs[0]
            hhmmss=splitstrs[1]
            datatype=splitstrs[-1]
            filename=datatype + '_' + YYYYMMDD + '_' + hhmmss + '.' + suffix
            localfilename=filename
        if self.datatype in http_stage3_datatype8:
            ##归档文件名，不做任何处理
            localfilename=filename    
            
        ####入库之前增加检查是否存在此数据，存在就跳过还是更新，暂时跳过
        # if(self.check_db(localfilename)):
            # print ('数据库中存在此数据！')
            # return
        # else:
            # print ('数据库中不存在此数据，需要入库！')
            # pass
        status_code = self.check_db(localfilename)
        print (type(status_code))
        print ('数据库检查完毕，返回状态码 %d '%status_code)
        if(status_code==0x000):
            print ('数据库中存在此数据，不需要入库！')
            return
        elif(status_code==0x001):
            print ('数据库中存在此数据，需要更新库！')
        # elif(status_code==0x002):
            # print ('数据库中不存在此数据，需要插入库！')
            ##pass        
        elif(status_code==0x002):
            print ('数据库为空 或者数据库中不存在此数据，需要插入库！')       
          
        #print (filename)
        #print (localfilename)
        
        #写文件使用绝对路径，需要读取cfg配置文件，写数据库写相对路径
        dataroot_path = configs['dataroot_path']
        print(configs)
        print ('dataroot_path = %s'%dataroot_path)        
        #localpath = os.path.join(dataroot_path,self.db_path,localfilename)
        localpath = dataroot_path + self.db_path
        localfullpath = localpath + localfilename
        ###存放数据的路径,需要根路径+相对路径
        #print (self.db_path)
        if not os.path.exists(localpath):
            os.makedirs(localpath)
            print("makedir...... %s" % localpath)
                
                
        print ('localfullpath = %s'%localfullpath)
        #localpath = os.path.join(self.db_path,localfilename)        
        try:
            f = open(localfullpath, 'wb')  # './img'为源文件夹的下一个文件夹,而最后的img.jpg就是最终的文件
        except Exception as e:
            #raise Exception(str(e))
            raise Exception(traceback.format_exc())            
        ##暂时注释掉,下载费流量和时间
        f.write(r.content)
        f.close()#需要关闭,否则下次使用，网址会被占用
        print ('数据存入本地磁盘 %s'%localfullpath)
        
        ####写磁盘的时候,入库,入库放到for循环外面比较麻烦
        self.db_filename=localfilename
        self.db_path=self.db_path
        self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        self.db_file_size=os.path.getsize(localfullpath)

        
        if(status_code==0x002):     
        #if(status_code==0x002)or(status_code==0x003):
            self.db_state=True
            self.db_log='成功'
            self.record_db()
            print("record_db finished!")
        if(status_code==0x001):
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
        
        #self.record_db()    
        return
    

    
    def down_https(self, url, starttime, endtime, expr):
        print ('into down_https...')
        print ('expr = %s'%expr)
        print ('url = %s'%url)
               
        subimglist=[]##需要剔除excel表格里不存在的gif图像
        ####模糊匹配完，需要剔除某些不符合条件的

        ####特殊情况，不需要模糊匹配
        ####kp_index数据，正则表达式匹配网页数据比较特殊,不需要正则表达式，直接拼接网址全链接
        if self.datatype in http_stage2_datatype2:
            print ('http_stage2_datatype2...')     
            imglist=expr
            if(imglist):
                pass
            else:
                ####没有网页数据，直接入库，失败信息写入数据库
                self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.record_db() 
                return
            resp,resp.status_code = self.getfullURL(url,imglist)
                    
            ##todo
            ####先判断r.status_code是否正常，因为直接拼接的网站全路径，可能没有数据
            if(404==resp.status_code):
                pass
            else:
                pass
                
            self.record_data(resp,imglist,starttime)
            return##没有匹配的，exp需要特殊处理
        
        if self.datatype in http_stage2_datatype3:
            print ('http_stage2_datatype3...')
            imglist=expr
            if(imglist):
                pass
            else:
                ####没有网页数据，直接入库，失败信息写入数据库
                self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.record_db() 
                return
            resp,resp.status_code  = self.getfullURL(url,imglist)
            print ('imglist = %s'%imglist)
            ##存本地路径，把html内容写成txt即可
            
            ####暂时不用txt文本文件，使用解析html库直接解析html文件即可
            #imglist = imglist.replace('html','txt')
            #print ('html文件后缀名，替换成txt = %s'%imglist)
            
            self.record_data(resp,imglist,starttime)
            return##没有匹配的，exp需要特殊处理
        
        
        #需要针对GMU_SOHO_COR2数据，进行特殊处理，找到时间最近的数据，12分钟1次，需要找到
        ####如果没有datatype分类的，需要正则表达式匹配获取
        try:
            html,req_status_code = self.gethtml(url)
        except Exception as e:
            raise Exception (e)            
        if(req_status_code==404):
            ####没有匹配到网页
            #print ('html==None...')
            self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #self.db_log='%s 不存在'%url
            pattern=r'(<p>.*?</p>)'
            infos = re.findall(pattern,html)##infos是[]，需要转换成字符串
            print ('infos = %s'%infos[0])
            self.db_log=infos[0]
            self.record_db() 
            return
        
        #print(html)
        print ('按正则表达式，查找html...')
        imglist = re.findall(expr,html)
        print('imglist = %s'%imglist)
        print('imglist len = %d'%len(imglist))
        if(imglist):
            pass
        else:
            ####没有网页数据，直接入库，失败信息写入数据库
            self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db_log='%s , 网站上不存此时间段的产品!'%expr
            self.record_db() 
            return
        #print('imglist = %s'%imglist)
        for l in imglist:
            resp,resp.status_code  = self.getfullURL(url,l)
            self.record_data(resp,l,starttime)
        return
    
    
    def start(self, starttime, endtime):
        self.get_sql_info()
        self.starttime = starttime        # 下载配置的开始时间
        self.endtime = endtime            # 下载配置的结束时间
        self.db_category_id = self.category_id##每种大类数据self.db_category_id不变
        
        # 循环时间
        while starttime <= endtime:
            yyyy = starttime[0:4]
            mm = starttime[4:6]
            dd = starttime[6:8]
            yymm = starttime[2:6]   #1910,19年10月
            yymmdd = starttime[2:8] #191022,19年10月22
            yyyymm = starttime[0:6]
            hhmmss=starttime[8:14]
            hhmm=starttime[8:12]
            yyyymmdd=starttime[0:8]
            yyyymmddhhmm=starttime[0:12]
            yyyymmddhhmmss=starttime
            print(yyyymmddhhmmss)
            
            ####换算开始，结束时间，入库时需要
            self.db_start_time=datetime.datetime.strptime(self.starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
            self.db_end_time=datetime.datetime.strptime(self.endtime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
            
            ####此处不能使用savepath，for循环中，替换1次，第2次就找不到YYYYMMDD字符串了
            ####修改路径db_path
            #self.db_path=self.savepath.replace('YYYYMMDD',str(yyyymmdd))
            ####替换3次
            # self.savepath=self.savepath.replace('YYYY',str(yyyy))
            # self.savepath=self.savepath.replace('MM',str(mm))
            # self.db_path=self.savepath.replace('DD',str(dd))
            ####先替换YYYYMMDD，否则可能找不到YYYYMMDD
            self.savepath=self.savepath.replace('YYYYMMDD',str(yyyymmdd))             
            self.db_path=self.savepath.replace('YYYYMM',str(yyyymm))

            
            ####存放数据的路径,需要根路径+相对路径
            # print (self.db_path)
            # if not os.path.exists(self.db_path):
                # os.makedirs(self.db_path)
                # print("makedir %s" % self.db_path)

            ####暂时取消band不行
            # bands = list(self.band.split(","))
            # for band in bands:
                ####网址需要特殊处理，不同网址，链接不同处理
            if self.datatype in http_stage1_datatype1:
                DOY=self.get_DOY(int(yyyy),int(mm),int(dd))
                ####self.url不能替换，for循环替换全局变量，导致下一次for循环找不到DOY字符串
                url=self.url.replace('DOY',str(DOY))            #replace替换完，需要赋值，否则exp的内容没有更改
                url=url.replace('YYYY',str(yyyy))               #replace替换完，需要赋值，否则exp的内容没有更改
                print('url = %s'%url)                    
                exp=self.exp.replace('YYYYMMDD',str(yyyymmdd))  #replace替换完，需要赋值，否则exp的内容没有更改
                print('exp = %s'%exp)
                try:
                    self.down_https(url, yyyymmddhhmmss, endtime, exp)
                except Exception as e:
                    raise Exception(e)

            if self.datatype in http_stage1_datatype2:
                url=self.url.replace('YYYY',str(yyyy))  
                ##需要处理正则表达式
                exp=self.exp.replace('yyyymmdd',str(yyyymmdd))  #replace替换完，需要赋值，否则exp的内容没有更改
                try:
                    self.down_https(url,yyyymmddhhmmss,endtime,exp)
                except Exception as e:
                    raise Exception(e)            
            if self.datatype in http_stage1_datatype3:                   
                url = self.url+'/'+ band+'/'
                print('url = %s'%url)
                try:
                    self.down_https(url, yyyymmddhhmmss, endtime, self.exp)
                except Exception as e:
                    raise Exception(e)            
            if self.datatype in http_stage1_datatype4:
                url=self.url.replace('YYYY',str(yyyy))
                url=url.replace('MM',str(mm))
                #url=url.replace('DD',str(dd)) 
                ##需要处理正则表达式
                exp=self.exp.replace('YYYYMMDD',str(yyyymmdd))  #replace替换完，需要赋值，否则exp的内容没有更改
                exp=exp.replace('hhmm',str(hhmm))               #replace,hhmm，使用href抓取，不需要ss；如果是直接拼接需要ss
                print('exp = %s'%exp)
                try:
                    self.down_https(url,yyyymmddhhmmss,endtime,exp)
                except Exception as e:
                    raise Exception(e)                
            if self.datatype in http_stage1_datatype5:
                try:
                    self.down_https(self.url,yyyymmddhhmmss,endtime,self.exp)               
                except Exception as e:
                    raise Exception(e)            
            if self.datatype in http_stage1_datatype6:
                exp=self.exp.replace('YYMM',str(yymm))
                try:
                    self.down_https(self.url,yyyymmddhhmmss,endtime,exp) 
                except Exception as e:
                    raise Exception(e)                
            if self.datatype in http_stage1_datatype7:
                url=self.url.replace('YYYY',str(yyyy))
                url=url.replace('MM',str(mm))
                url=url.replace('DD',str(dd)) 
                ##需要处理正则表达式
                exp=self.exp.replace('YYMMDD',str(yymmdd))      #replace替换完，需要赋值，否则exp的内容没有更改
                exp=exp.replace('hhmm',str(hhmm))               #replace,hhmm，使用href抓取，不需要ss；如果是直接拼接需要ss
                print('exp = %s'%exp)
                print('url = %s'%url)
                try:
                    self.down_https(url,yyyymmddhhmmss,endtime,exp)
                except Exception as e:
                    raise Exception(e)            
            if self.datatype in http_stage1_datatype8:
                url=self.url.replace('YYYY',str(yyyy))
                url=url.replace('MM',str(mm))
                url=url.replace('DD',str(dd))
                self.exp=self.exp.replace('YYYYMMDD',str(yyyymmdd))
                exp=self.exp.replace('hhmmss',str(hhmmss)) 
                print('url = %s'%url)
                try:
                    self.down_https(url,yyyymmddhhmmss,endtime,exp)                    
                except Exception as e:
                    raise Exception(e)
                    
            ####特殊情况占大多数
            yyyymmddhhmmss = (datetime.datetime.strptime(yyyymmddhhmmss, "%Y%m%d%H%M%S") + datetime.timedelta(days=1)).strftime("%Y%m%d%H%M%S")
            starttime=yyyymmddhhmmss####日期自动加1，更新开始时间
        #return db_infos
        
        return

