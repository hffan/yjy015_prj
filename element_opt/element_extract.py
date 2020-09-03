# -*- coding: utf-8 -*-
##要素提取，入库




"""
@modify history
2020-05-09 15:05:23
                    1. 要素提取，根据数据库查询的路径和文件名，结合读取配置文件中数据存放的绝对路径的根路径
2020-08-07 10:48:43
                    1. SWPC_GOES_DE5m，SWPC_GOES_DP5m,没有要素提取，但是data_category表里，element_extract_flag错误的改为true,应该是false
                    
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


import element_opt.read_kp_ap_html
import element_opt.read_DGD

import element_opt.read_dst
import element_opt.read_f107
import element_opt.read_rad
import element_opt.read_ssn
import element_opt.read_DSD
import element_opt.read_sao
import element_opt.read_hpi
import element_opt.read_sta_mag_1m
import element_opt.read_sta_plastic_1m
import element_opt.read_sta_het_5m
import element_opt.read_ace_swepam_1m
import element_opt.read_ace_mag_1m
import element_opt.read_ace_epam_5m
import element_opt.read_ace_sis_5m
import element_opt.read_goes_xray
import element_opt.read_goes_mag
import element_opt.read_goes_int_proton
import element_opt.read_goes_int_eletron


from cfg.conf import *
from sys_interface.sys_str import *



class ElementExtract:
    # 初始化
    def __init__(self,datatype,path,filename):
        self.datatype       = datatype
        self.path           = path
        self.filename       = filename


        self.fullfilepath   =  configs['rootpath'] + '/' + path #path为数据库中查询到的相对路径
        #self.fullfilename   = self.fullfilepath + self.filename
        self.fullfilename   = os.path.join(self.fullfilepath,self.filename)
 
    def get_data(self):
        ##如果没有匹配符合条件的，默认返回空字典    
        data1_dicts={}
        data2_dicts={}

        ##默认data2_dicts是空，为了匹配kp,ap同时入库这种情况
        if self.datatype == 'GFZ_Kp_web':
            data1_dicts,data2_dicts = element_opt.read_kp_ap_html.read_data(self.fullfilename)
        if self.datatype == 'SWPC_latest_DGD':
            data1_dicts,data2_dicts = element_opt.read_DGD.read_data(self.fullfilename)            
        if self.datatype == 'KYOTO_Dst_web':
            data1_dicts = element_opt.read_dst.read_data(self.fullfilename)
        if self.datatype == 'NRCAN_F107_txt':
            data1_dicts = element_opt.read_f107.read_data(self.fullfilename)      
        if self.datatype == 'SWPC_Solar_rad':
            data1_dicts = element_opt.read_rad.read_data(self.fullfilename)      
        if self.datatype == 'SIDC_SN_dat':
            data1_dicts = element_opt.read_ssn.read_data(self.fullfilename)
        if self.datatype == 'SWPC_latest_DSD':
            data1_dicts = element_opt.read_DSD.read_data(self.fullfilename)
        if self.datatype == 'NGDC_BP440_SAO':
            data1_dicts = element_opt.read_sao.read_data(self.fullfilename)
        if self.datatype == 'SWPC_Aurora_hpi':
            data1_dicts = element_opt.read_hpi.read_data(self.fullfilename)
        if self.datatype == 'SWPC_STEA_mag':
            data1_dicts = element_opt.read_sta_mag_1m.read_data(self.fullfilename)
        if self.datatype == 'SWPC_STEA_plastic':
            data1_dicts = element_opt.read_sta_plastic_1m.read_data(self.fullfilename)            
        if self.datatype == 'SWPC_STEA_het':
            data1_dicts = element_opt.read_sta_het_5m.read_data(self.fullfilename)   
        if self.datatype == 'SWPC_ace_sw1m':
            data1_dicts = element_opt.read_ace_swepam_1m.read_data(self.fullfilename)   
        if self.datatype == 'SWPC_ace_mag1m':
            data1_dicts = element_opt.read_ace_mag_1m.read_data(self.fullfilename)   
        if self.datatype == 'SWPC_ace_ep5m':
            data1_dicts = element_opt.read_ace_epam_5m.read_data(self.fullfilename)   
        if self.datatype == 'SWPC_ace_sis5m':
            data1_dicts = element_opt.read_ace_sis_5m.read_data(self.fullfilename)  
        if self.datatype == 'SWPC_GOES_XR1m':
            data1_dicts = element_opt.read_goes_xray.read_data(self.fullfilename)  
        if self.datatype == 'SWPC_GOES_mag1m':
            data1_dicts = element_opt.read_goes_mag.read_data(self.fullfilename)
        if self.datatype == 'SWPC_GOES_IP5m':
            data1_dicts = element_opt.read_goes_int_proton.read_data(self.fullfilename) 
        if self.datatype == 'SWPC_GOES_IE5m':
            data1_dicts = element_opt.read_goes_int_eletron.read_data(self.fullfilename)             
            
        return data1_dicts,data2_dicts
        
        
        
        