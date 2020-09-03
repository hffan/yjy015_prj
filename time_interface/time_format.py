# -*- coding: UTF-8 -*-

import os
import datetime



"""
@modify history

2020-05-09 14:27:11
                    1. 获取系统UTC时间，调度任务启动使用utc时间，获取系统时间也需要获取系统的UTC时间，因为系统默认配置的UTC+8，北京时区
                    
                    
                    

"""
def get_current_BJT():
    """获取当前时间，当前时分秒"""
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hour = datetime.datetime.now().strftime("%H")
    mm = datetime.datetime.now().strftime("%M")
    ss = datetime.datetime.now().strftime("%S")
    #return now_time, hour, mm, ss
    return now_time      

    
def get_current_UTC():
    """获取当前时间，当前时分秒"""
    now_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    hour = datetime.datetime.utcnow().strftime("%H")
    mm = datetime.datetime.utcnow().strftime("%M")
    ss = datetime.datetime.utcnow().strftime("%S")
    #return now_time, hour, mm, ss
    return now_time      
    
    
    
def get_yesterday_UTC():
    """获取昨天时间，时分秒"""
    
    yesterday_time = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    # now_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    # hour = datetime.datetime.utcnow().strftime("%H")
    # mm = datetime.datetime.utcnow().strftime("%M")
    # ss = datetime.datetime.utcnow().strftime("%S")
    # return now_time, hour, mm, ss
    return yesterday_time      
        
    
    
    
