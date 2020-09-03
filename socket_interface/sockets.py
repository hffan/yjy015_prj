# -*- coding: UTF-8 -*-

import os
import socket
import getpass

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    # print('[INFO]: %s%s' % ('节点ip地址，', ip))
    #s_print('节点ip地址', ip)
    return ip

    
def get_username():
    """root"""
    user_name = getpass.getuser() # 获取当前用户名  
    return user_name

    
def get_hostname():
    """gtm"""
    host_name = socket.gethostname() # 获取当前主机名
    return host_name
    
    
    
    
    
    