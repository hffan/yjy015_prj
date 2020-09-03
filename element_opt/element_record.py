# -*- coding: UTF-8 -*-
##要素提取，入库
"""
@modify history
2020-05-26 14:18:05
                    1. 实际测试入库的字段，int,str,类型，python插入库的时候，int，str类型都可以,最终插入数据库里的值是数据库里规定的数据类型
2020-06-01 10:39:21
                    1. 数据库名，统一由conf配置文件获取
2020-08-11 13:13:09
select * from element_ace_ep ORDER BY utc_time
select * from element_ace_mag ORDER BY utc_time
select * from element_ace_sis ORDER BY utc_time
select * from element_ace_sw ORDER BY utc_time
select * from element_ap ORDER BY utc_time
select * from element_dst ORDER BY utc_time
select * from element_f107 ORDER BY utc_time
select * from element_goes_ie ORDER BY utc_time
select * from element_goes_ip ORDER BY utc_time
select * from element_goes_mag ORDER BY utc_time
select * from element_goes_xr ORDER BY utc_time
select * from element_hpi ORDER BY utc_time
select * from element_kp ORDER BY utc_time
select * from element_rad ORDER BY utc_time             --同一个utc_time时间,对应多条记录
select * from element_ssn ORDER BY utc_time
select * from element_ste_het ORDER BY utc_time
select * from element_ste_mag ORDER BY utc_time
select * from element_ste_sw ORDER BY utc_time
select * from element_swpc_flare ORDER BY utc_time
select * from element_tec ORDER BY utc_time



                    
"""
import os
import requests
import re
import datetime
import time
import xml.etree.ElementTree as ET
from logger.logger import *
from urllib.request import urlopen
from bs4 import BeautifulSoup
from lxml import etree
from db.postgres_table import *
from db.postgres_archive import *
from cfg.conf import *


class ElementRecord:
    # 初始化
    def __init__(self,datatype):
       
        ####归档入库的所有全局变量定义，加db前缀
        ####如果数据处理异常、失败，使用此全局变量入库
        # self.db_record_time = ''            # 入库时间
        # self.db_time = ''                   # 观测时间
        # self.db_website=''                  # 全局变量，可以在程序中使用此变量，记录实际的错误信息
        # self.db_category_abbr_en=''         # 全局变量，可以在程序中使用此变量，记录实际的错误信息
        self.category_abbr_en=datatype
    
    
    #def cal_IEFday(self,EFgt2d0Ms):
    def cal_IEFday(self,utc_time):
        """
        1. 查找当天时刻对应的积分通量-9999,并修改当天积分通量
        2. SELECT * FROM data_file_info WHERE category_abbr_en = 'SWPC_GOES_IE5m' and  start_time >= '2020-07-01 00:00:00'
        3. DELETE from data_file_info WHERE category_abbr_en = 'SWPC_GOES_IE5m' and  start_time >= '2020-07-01 00:00:00'
        4. cd /home/YJY015/code; python3 /home/YJY015/code/download.py SWPC_GOES_IE5m 20200702000000 20200702000000
        5. utc_time = '2020-07-02 08:00:00'
           utc_time_24h = ( datetime.datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=1) + datetime.timedelta(minutes=5) ).strftime("%Y-%m-%d %H:%M:%S")
           utc_time_24h = '2020-07-01 08:00:00'
        6. 查询289条,需要剔除第1条 
        7. SELECT * FROM element_goes_ie WHERE utc_time between '2020-07-01 08:05:00' and '2020-07-02 08:00:00' ORDER BY utc_time
        """
        db_name     =   configs['db_name']
        table_name  =   'element_goes_ie'
        pga         =   PostgresArchive() 
        
        utc_time_24h = ( datetime.datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=1) + datetime.timedelta(minutes=5) ).strftime("%Y-%m-%d %H:%M:%S")
        
        sqlcmd="SELECT * FROM %s WHERE utc_time between '%s' and '%s'"%(table_name,utc_time_24h,utc_time)
        #print (sqlcmd)
        searchinfos=pga.search_db_table_usercmd(db_name,sqlcmd)
        
        EFgt2d0Ms = []
        if(searchinfos):#数据库不为空
            for searchinfo in searchinfos:                
                efgt2d0m = float(searchinfo['efgt2d0m'])
                EFgt2d0Ms.append(efgt2d0m)                

        # 功能：计算2MeV电子日积分通量，双精度实数
        # 输入：过去24小时2MeV通量，每五分钟一个值，共288个值（可能小于288个），查询EFgt2d0M得到
        # 输出：IEFday，双精度实数
        # 4是默认值
        IEFday=0
        if len(EFgt2d0Ms)>288:
            #print('输入个数大于288个')
            #IEFday=4*86400  
            IEFday=4*288*5*60
            #return 
        else:
            for EFgt2d0M in EFgt2d0Ms:
                IEFday=IEFday+EFgt2d0M*(5*60)
        
        ####对IEFday进行更新操作
        sqlcmd="update %s set iefday = '%s' where utc_time = '%s'"%(table_name,IEFday,utc_time)
        #print (sqlcmd)
        searchinfos=pga.insert_db_table_usercmd(db_name,sqlcmd)        
        
        return 
    
    def get_table_name(self):
        """返回的table_name,list类型，匹配解决同时入库多个table情况"""
        if self.category_abbr_en == 'NRCAN_F107_txt':
            table_name = ['element_f107']
        if self.category_abbr_en == 'SWPC_Solar_rad':
            table_name = ['element_rad'  ]       
        if self.category_abbr_en == 'SIDC_SN_dat':
            table_name = ['element_ssn']
        if self.category_abbr_en == 'SWPC_latest_DSD':
            table_name = ['element_swpc_flare']
        # #if self.category_abbr_en == 'SWPC_latest_DGD' or self.category_abbr_en == 'GFZ_Kp_tab':            
        # if self.category_abbr_en == 'SWPC_latest_DGD' or self.category_abbr_en == 'GFZ_Kp_web':
            # table_name = 'kp'
        # #if self.category_abbr_en == 'SWPC_latest_DGD' or self.category_abbr_en == 'GFZ_Kp_tab':            
        # if self.category_abbr_en == 'SWPC_latest_DGD' or self.category_abbr_en == 'GFZ_Kp_web':
            # table_name = 'ap'
        if self.category_abbr_en == 'SWPC_latest_DGD' or self.category_abbr_en == 'GFZ_Kp_web':
            table_name = ['element_kp','element_ap']         
        if self.category_abbr_en == 'KYOTO_Dst_web':
            table_name = ['element_dst']
        if self.category_abbr_en == 'NGDC_BP440_SAO':
            table_name = ['element_tec']
        if self.category_abbr_en == 'SWPC_Aurora_hpi':
            table_name = ['element_hpi']
        ##2种数据合成1个表，需要先插1种数据，后更新另1种数据
        if self.category_abbr_en == 'SWPC_STEA_plastic':
            table_name = ['element_ste_sw']
        if self.category_abbr_en == 'SWPC_STEA_mag':
            table_name = ['element_ste_mag']            
        ##2种数据合成1个表，需要先插1种数据，后更新另1种数据
        if self.category_abbr_en == 'SWPC_STEA_het':
            table_name = ['element_ste_het']
        ##2种数据合成1个表，需要先插1种数据，后更新另1种数据
        if self.category_abbr_en == 'SWPC_ace_sw1m':
            table_name = ['element_ace_sw']
        if self.category_abbr_en == 'SWPC_ace_mag1m':
            table_name = ['element_ace_mag']            
        ##2种数据合成1个表，需要先插1种数据，后更新另1种数据
        if self.category_abbr_en == 'SWPC_ace_ep5m':
            table_name = ['element_ace_ep']
        if self.category_abbr_en == 'SWPC_ace_sis5m':
            table_name = ['element_ace_sis']            
        ##2种数据合成1个表，需要先插1种数据，后更新另1种数据
        # if self.category_abbr_en == 'SWPC_Gp_XR1m' or \
           # self.category_abbr_en == 'SWPC_Gs_XR1m' or \
           # self.category_abbr_en == 'SWPC_Gp_XR5m' or \
           # self.category_abbr_en == 'SWPC_Gs_XR5m':
        if self.category_abbr_en == 'SWPC_GOES_XR1m':                      
            table_name = ['element_goes_xr']
        if self.category_abbr_en == 'SWPC_GOES_mag1m':            
        # if self.category_abbr_en == 'SWPC_Gp_mag1m'or self.category_abbr_en == 'SWPC_Gs_mag1m':
            table_name = ['element_goes_mag']            
        #if self.category_abbr_en == 'SWPC_Gp_part5m'or self.category_abbr_en == 'SWPC_Gs_part5m':            
        if self.category_abbr_en == 'SWPC_GOES_IE5m':
            table_name = ['element_goes_ie']     
        if self.category_abbr_en == 'SWPC_GOES_IP5m':
            table_name = ['element_goes_ip']               
        return table_name
    
    
    ##数据入库
    def insert_db(self,table_name,config_infos):
        #print ('insert_db......')
        #db_name = 'yjy015'
        db_name = configs['db_name']    
        pga=PostgresArchive()
        #pga.insert_db_table('element_db','file_info',config_infos)
        pga.insert_db_table(db_name,table_name,config_infos)    
        #pga.insert_db_table('element_db',table_name,config_infos)           
        return 
    
    
    ##核对数据库里是否存在此数据，
    ##category_id,filename相同，就是同1个数据;或者数据库为空和2个条件不全满足的可以入库 
    def check_db(self,table_name,condition_infos):
        #print ('check_db......')
        #db_name = 'yjy015'
        db_name = configs['db_name']  
        pga=PostgresArchive() 
        #searchinfos=pga.search_db_table('element_db',table_name,condition_infos)
        searchinfos=pga.search_db_table(db_name,table_name,condition_infos)
        #print (searchinfos)
        if(searchinfos):#数据库不为空
            searchinfo=searchinfos[0]#暂时默认只取第一个list的内容
            #utc_time = searchinfo['utc_time']
               
            ##查询时间不为空，而且时间只能有1个，如果查询到，即认为时间能匹配到，数据库里有此数据，不需要再入库
            #print ('return 0')
            return 0x000
            ####这种情况不存在，因为查询的时候，是filename，category_id同时为查询条件
            # elif(category_id!=self.db_category_id) or (filename!=self.db_filename):
                # print ('return 2')
                # return 2
        ##数据库为空
        else:
            #print ('return 1')
            return 0x001
        
        
    ##记录数据库
    ##0x000 数据库中存在此数据，不需要入库
    ##0x001 数据库为空或数据库中不存在此数据，需要插入库
    
    def record_data(self,table_name,config_infos,condition_infos):
        #print ('record_data......')

        status_code = self.check_db(table_name,condition_infos)
        #print (type(status_code))
        #print ('数据库检查完毕，返回状态码 %d '%status_code)
        if(status_code==0x000):
            #print ('数据库中存在此数据，不需要入库！')
            return  
        elif(status_code==0x001):
            #print ('数据库为空 或者数据库中不存在此数据，需要插入库！')       
            pass
        
        #self.db_record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')       
        if(status_code==0x001):     
            self.insert_db(table_name,config_infos)
            #print("insert_db finished!")
        return

    ##key_l1:字典变量1级键值
    ##key_l2:字典变量2级键值
    ##key_l3:字典变量3级键值  
    ##函数实现，尽量和传入的变量解耦合，减少关联性，增加代码复用性
    def analysis_dicts(self,table_name,key_l1,dict_data):
        #print ('into analysis_dicts......')
        ##解析每个时间对应的字典值，dict_data的每个字典元素
        #print('table_name = %s'% table_name)
        ####根据不同的要素，来区分入库的表结构和入库的条件
        ####根据表名来区分，category_abbr_en来区分有好多种情况，后期的数据有可能变更导致有bugs
        if table_name == 'element_f107':
            utc_time = key_l1
            #julian = dict_data['julian']
            carrington   = dict_data['carrington']
            obsflux = dict_data['obsflux']
            adjflux = dict_data['adjflux']
            ursiflux = dict_data['ursiflux']
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            #'julian':julian,
            'carrington':carrington,
            'obsflux':obsflux,
            'adjflux':adjflux,               
            'ursiflux':ursiflux,
            'website':website,            
            'category_abbr_en':category_abbr_en}
            
            ##数据库查询utc_time即可区分
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)
            
            
        if table_name == 'element_rad':
            ##dict_data在参数传入的时候,已经是第2级的数据,dict_data=dict_datas[key_l1]
            ##字典嵌套3层，第1层时间，第2层站名称，第3层频点
            for key_l2 in dict_data.keys():
                #print (dict_datas[key])
                for key_l3 in dict_data[key_l2].keys():
                    utc_time = key_l1
                    station = key_l2
                    freq   = key_l3
                    flux = dict_data[key_l2][key_l3]['flux']
                    website = dict_data[key_l2][key_l3]['website']
                    category_abbr_en = dict_data[key_l2][key_l3]['category_abbr_en']
                    
                    config_infos = {
                    'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'utc_time':utc_time,
                    'station':station,
                    'freq':freq,
                    'flux':flux,
                    'website':website,            
                    'category_abbr_en':category_abbr_en}
                    ##数据库查询utc_time,station,freq即可区分
                    condition_infos = {
                        'utc_time':utc_time,
                        'station':station,
                        'freq':freq}
                    ####入库
                    self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_ssn':
            utc_time = key_l1
            sn = dict_data['sn']
            std   = dict_data['std']
            num_obs = dict_data['num_obs']
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'sn':sn,
            'std':std,
            'num_obs':num_obs,
            'website':website,            
            'category_abbr_en':category_abbr_en}           
            ##数据库查询utc_time即可区分
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)


        if table_name == 'element_swpc_flare':
            utc_time = key_l1
            F107 = dict_data['F107']##excel表格F107，接口data键值f107，访问不到键值，区分大小写
            SunspotNum   = dict_data['SunspotNum']
            SunspotArea = dict_data['SunspotArea']
            NewRegions = dict_data['NewRegions']
            XRayBkgdFlux = dict_data['XRayBkgdFlux']
            FlaresXRayC = dict_data['FlaresXRayC']
            FlaresXRayM = dict_data['FlaresXRayM']
            FlaresXRayX = dict_data['FlaresXRayX']
            FlaresOpticalS = dict_data['FlaresOpticalS']
            FlaresOptical1 = dict_data['FlaresOptical1']
            FlaresOptical2 = dict_data['FlaresOptical2']
            FlaresOptical3 = dict_data['FlaresOptical3']
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'F107':F107,
            'SunspotNum':SunspotNum,
            'SunspotArea':SunspotArea,
            'NewRegions':NewRegions,
            'XRayBkgdFlux':XRayBkgdFlux,
            'FlaresXRayC':FlaresXRayC,
            'FlaresXRayM':FlaresXRayM,
            'FlaresXRayX':FlaresXRayX,
            'FlaresOpticalS':FlaresOpticalS,
            'FlaresOptical1':FlaresOptical1,
            'FlaresOptical2':FlaresOptical2,
            'FlaresOptical3':FlaresOptical3,            
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time即可区分
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_kp':
            utc_time = key_l1
            #kp = dict_data['kp']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            kp = dict_data['Kp']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            level = dict_data['level']
            descrip = dict_data['descrip']            
            website = dict_data['website']            
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'kp':kp,
            'level':level,
            'descrip':descrip,            
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time,website,category_abbr_en ，3种组合判断
            condition_infos = {'utc_time':utc_time,'website':website,'category_abbr_en':category_abbr_en}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_ap':
            utc_time = key_l1
            ap = dict_data['Ap']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'ap':ap,           
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            #condition_infos = {'utc_time':utc_time}
            condition_infos = {'utc_time':utc_time,'website':website,'category_abbr_en':category_abbr_en}            
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)


        if table_name == 'element_dst':
            utc_time = key_l1
            Dst = dict_data['Dst']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'Dst':Dst,           
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_tec':
            utc_time = key_l1
            site    = dict_data['site']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            TEC     = dict_data['TEC']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            foF2 = dict_data['foF2']
            foF1 = dict_data['foF1']
            M = dict_data['M']
            MUF = dict_data['MUF']
            fmin = dict_data['fmin']
            website = dict_data['website']            
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'site':site,
            'TEC':TEC,
            'foF2':foF2,               
            'foF1':foF1,               
            'M':M,               
            'MUF':MUF,               
            'fmin':fmin,                           
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time,'site':site}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_hpi':
            utc_time = key_l1
            NorthHPI = dict_data['NorthHPI']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            SouthHPI = dict_data['SouthHPI']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']
            #if category_abbr_en == 'NRCAN_F107_txt':
            
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'NorthHPI':NorthHPI,
            'SouthHPI':SouthHPI,               
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

            
        if table_name == 'element_ste_sw':
            utc_time = key_l1
            satellite = 'STEREO A'##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Density = dict_data['Density']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Speed = dict_data['Speed']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Temp = dict_data['Temp']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'Density':Density,
            'Speed':Speed,
            'Temp':Temp,                                   
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time,'satellite':satellite}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

        if table_name == 'element_ste_mag':
            utc_time = key_l1
            satellite = 'STEREO A'##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            BR = dict_data['BR']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            BT = dict_data['BT']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            BN = dict_data['BN']
            Btotal = dict_data['Btotal']
            Lat = dict_data['Lat']
            Lon = dict_data['Lon']
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,                   
            'BR':BR,
            'BT':BT,
            'BN':BN,
            'Btotal':Btotal,
            'Lat':Lat,   
            'Lon':Lon,                
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time,'satellite':satellite}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)
            
        if table_name == 'element_ste_het':
            utc_time = key_l1
            satellite = 'STEREO A'                                                      ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            ProFlux_13to21Mev = dict_data['ProFlux_13to21Mev']
            ProFlux_40to100Mev = dict_data['ProFlux_40to100Mev']           
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'ProFlux_13to21Mev':ProFlux_13to21Mev,
            'ProFlux_40to100Mev':ProFlux_40to100Mev,             
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time,'satellite':satellite}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)
            
            
        if table_name == 'element_ace_sw':
            utc_time = key_l1
            Density = dict_data['Density']  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Speed = dict_data['Speed']      ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Temp = dict_data['Temp']        ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写               
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'Density':Density,
            'Speed':Speed,
            'Temp':Temp,                          
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)            
            
            
        if table_name == 'element_ace_mag':
            utc_time = key_l1               
            S = dict_data['S']              ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写         
            Bx = dict_data['Bx']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            By = dict_data['By']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Bz = dict_data['Bz']
            Bt = dict_data['Bt']
            Lat = dict_data['Lat']
            Lon = dict_data['Lon']
            Bx_GSE = dict_data['Bx_GSE']
            By_GSE = dict_data['By_GSE']
            Bz_GSE = dict_data['Bz_GSE']
            website = dict_data['website']
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'S':S,            
            'Bx':Bx,
            'By':By,
            'Bz':Bz,
            'Bt':Bt,
            'Lat':Lat,   
            'Lon':Lon,
            'Bx_GSE':Bx_GSE,
            'By_GSE':By_GSE,            
            'Bz_GSE':Bz_GSE,            
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}
            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)    

            
        if table_name == 'element_ace_ep':
            utc_time = key_l1
            EleS = dict_data['EleS']  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            EleDiffFlux_38to53 = dict_data['EleDiffFlux_38to53']  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            EleDiffFlux_175to315 = dict_data['EleDiffFlux_175to315']  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            ProS = dict_data['ProS']  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            ProDiffFlux_47to68 = dict_data['ProDiffFlux_47to68']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            ProDiffFlux_115to195 = dict_data['ProDiffFlux_115to195']##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            ProDiffFlux_310to580 = dict_data['ProDiffFlux_310to580']
            ProDiffFlux_795to1193 = dict_data['ProDiffFlux_795to1193']
            ProDiffFlux_1060to1900 = dict_data['ProDiffFlux_1060to1900']       
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'EleS':EleS,
            'EleDiffFlux_38to53':EleDiffFlux_38to53,
            'EleDiffFlux_175to315':EleDiffFlux_175to315,            
            'ProS':ProS,            
            'ProDiffFlux_47to68':ProDiffFlux_47to68,
            'ProDiffFlux_115to195':ProDiffFlux_115to195,
            'ProDiffFlux_310to580':ProDiffFlux_310to580,
            'ProDiffFlux_795to1193':ProDiffFlux_795to1193,
            'ProDiffFlux_1060to1900':ProDiffFlux_1060to1900,
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)                
            

        if table_name == 'element_ace_sis':
            utc_time = key_l1
            ProFlux_GT10MeV = dict_data['ProFlux_GT10MeV']
            ProFlux_GT30MeV = dict_data['ProFlux_GT30MeV']           
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'ProFlux_GT10MeV':ProFlux_GT10MeV,
            'ProFlux_GT30MeV':ProFlux_GT30MeV,
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)   

            
        if table_name == 'element_goes_xr':
            utc_time = key_l1
            satellite = dict_data['satellite']                      ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            time_resolution = dict_data['time_resolution']          ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            XR_short = dict_data['XR_short']                        ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            XR_long = dict_data['XR_long']                          ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写           
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']
            level= dict_data['level']
            descrip= dict_data['descrip']            
            HAF= dict_data['HAF'] 

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'time_resolution':time_resolution,
            'XR_short':XR_short,            
            'XR_long':XR_long,
            'level':level,
            'descrip':descrip,
            'HAF':HAF,    
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time, 'satellite':satellite,'time_resolution':time_resolution}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)                
        
        
        if table_name == 'element_goes_mag':
            utc_time = key_l1
            satellite = dict_data['satellite']                      ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Hp = dict_data['Hp']        ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            He = dict_data['He']        ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写
            Hn = dict_data['Hn']        ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写     
            TotalField = dict_data['TotalField']                  ##excel表格F107，接口data键值f107，访问不到键值，字典是区分大小写                     
            website = dict_data['website']         
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'Hp':Hp,
            'He':He,            
            'Hn':Hn,
            'TotalField':TotalField,             
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time, 'satellite':satellite}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)
                
            
        if table_name == 'element_goes_ie':
            utc_time = key_l1
            satellite = dict_data['satellite']                        ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写 
            EFgt0d8M = dict_data['EFgt0d8M']                          ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写   
            EFgt2d0M = dict_data['EFgt2d0M']                          ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写   
            EFgt4d0M = dict_data['EFgt4d0M']                          ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写                 
            level = dict_data['level']
            descrip= dict_data['descrip']
            IEFday = dict_data['IEFday']         
            website = dict_data['website']                     
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'EFgt0d8M':EFgt0d8M,
            'EFgt2d0M':EFgt2d0M,
            'EFgt4d0M':EFgt4d0M,
            'level':level,    
            'descrip':descrip,    
            'IEFday':IEFday,                
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time, 'satellite':satellite}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)

            ####增加读数据库当前时刻之前1天的日积分通量值
            ####如果积分通量是-9999,需要更新积分通量的值
            if -9999 == IEFday:
                #print ('into if -9999 == IEFday:')
                #print (utc_time)
                #input()
                self.cal_IEFday(utc_time)
            
            
        if table_name == 'element_goes_ip':
            utc_time = key_l1
            satellite = dict_data['satellite']                          ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写
            PFgt01M = dict_data['PFgt01M']                              ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写
            PFgt05M = dict_data['PFgt05M']                              ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写
            PFgt10M = dict_data['PFgt10M']                              ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写     
            PFgt30M = dict_data['PFgt30M']                              ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写          
            PFgt50M = dict_data['PFgt50M']                              ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写   
            PFgt100M = dict_data['PFgt100M']                            ##excel表格F107，接口data键值f107，访问不到键值，字典键值是区分大小写                  
            Ad = dict_data['Ad']
            An = dict_data['An']
            level = dict_data['level']
            descrip = dict_data['descrip']
            website = dict_data['website']            
            category_abbr_en = dict_data['category_abbr_en']

            ####
            config_infos = {
            'record_time':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utc_time':utc_time,
            'satellite':satellite,
            'PFgt01M':PFgt01M,
            'PFgt05M':PFgt05M,            
            'PFgt10M':PFgt10M,
            'PFgt30M':PFgt30M,
            'PFgt50M':PFgt50M,
            'PFgt100M':PFgt100M,
            'Ad':Ad,
            'An':An,
            'level':level,            
            'descrip':descrip,            
            'website':website,            
            'category_abbr_en':category_abbr_en}   
            
            ##数据库查询utc_time判断
            condition_infos = {'utc_time':utc_time, 'satellite':satellite}            
            ####入库
            self.record_data(table_name,config_infos,condition_infos)


            
        return config_infos,condition_infos        
    
   
    
    
    
    def record_dicts(self,table_name,dict_data1,dict_data2):
        #print ('into record_dicts......')
        #print (table_name)
        #print ('len(table_name)) = %d'%len(table_name) )

        ####依次解析dict字典里的值
        for key in dict_data1.keys():
            # print (dict_datas[key])
            config_infos,condition_infos = self.analysis_dicts(table_name[0],key,dict_data1[key])
            
            ####入库，因为rad表比较特殊，嵌套3层字典，需要在for循环里入库
            #self.record_data(table_name,config_infos,condition_infos)
            #return config_infos,condition_infos  
            
        ####判断table_name维度，如果是2个，就使用dict_data2
        if (2==len(table_name)):
            for key in dict_data2.keys():
                # print (dict_datas[key])
                config_infos,condition_infos = self.analysis_dicts(table_name[1],key,dict_data2[key])           
        
        return 
    
    
    ##starttime从数据库查这个时间的数据，进行要素提取，再入库
    ##dict_data2默认为空，不传递参数，不使用dict_data2
    def record(self,table_name,starttime,dict_data1,dict_data2):
        ####utc时间解析
        yyyy = starttime[0:4]
        mm = starttime[4:6]
        dd = starttime[6:8]
        yymm = starttime[2:6]   #1910,19年10月
        yymmdd = starttime[2:8] #191022,19年10月22
        hhmmss=starttime[8:14]
        hhmm=starttime[8:12]
        yyyymmdd=starttime[0:8]
        yyyymmddhhmm=starttime[0:12]
        yyyymmddhhmmss=starttime
        #print(yyyymmddhhmmss)
        
        ####换算观测时间，入库时需要
        #self.db_time=datetime.datetime.strptime(starttime,'%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        
        ####解析dict_data,根据category_abbr_en返回的值唯一性，可以确定是哪个表，针对表返回的不同结果，就可以处理不同表的dict字典数据
        ####入库时1条记录1条记录的入库，但是dict_data有可能返回N个数据，需要在分析字典的for循环里入库
        self.record_dicts(table_name,dict_data1,dict_data2)
        
        # ####入库
        # record_data(table_name,config_infos,condition_infos)
        
        return
        
        
        