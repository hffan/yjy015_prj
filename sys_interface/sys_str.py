# -*- coding: UTF-8 -*-


import time
import sys
"""
cd /home/YJY015/code/sys_interface; python3 sys_str.py
"""



def find_first_dir(path):
    if(''==path.split("/",1)[0]):
        path=path.split("/",1)[1]
    else:
        dir = path.split("/",1)[0]
        rootpath = path.split("/",1)[1]
        return rootpath,dir
    #print (path)
    return find_first_dir(path)



def find_last_dir(path):
    if(''==path.rsplit("/",1)[-1]):
        path=path.rsplit("/",1)[-2]
    else:
        dir = path.rsplit("/",1)[-1]
        rootpath = path.rsplit("/",1)[-2]
        return rootpath,dir
    #print (path)
    return find_last_dir(path)
    
    
if __name__ == '__main__':
    path='/home/YJY015/data///'
    rootpath,dir_name = find_last_dir(path)
    print (rootpath)
    print (dir_name)
    
    
    
    