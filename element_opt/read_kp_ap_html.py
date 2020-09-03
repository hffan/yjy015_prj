# -*- coding: UTF-8 -*-
# from html_parser import *

from bs4 import BeautifulSoup
import os
from collections import defaultdict
import re
import datetime

def geomag_strom(P):    
    # 功能：地磁暴事件等级
    # 输入：地磁Kp指数
    # 输出：地磁暴等级，共4级别
    
    levels={
        'L1':'小',
        'L2':'中等',
        'L3':'大',
        'L4':'特大',
        'L5':'超大'}
    
    measures={
        'L1':5,
        'L2':6,
        'L3':7,
        'L4':8,
        'L5':9}
        
    descrips={
        'L1':'',
        'L2':'',
        'L3':'',
        'L4':'强',
        'L5':'超强'}
    
    descrip=''
    level=''
    for key in descrips:
        if P>=measures[key]:
            descrip=descrips[key]
            level=levels[key]
    return level,descrip
    
    
def merge_kp_dicts(date_str,kp_data):
    #dicts={}
    dicts = defaultdict(dict)
    ####
    ####March 15, 2020
    datetime_format = datetime.datetime.strptime(date_str, '%B %d, %Y')

    year = datetime_format.year
    month = datetime_format.month

    # # 取年
    # print(datetime_format.year)
    # # 取月
    # print(datetime_format.month)
    for key_l1 in kp_data.keys():
        day = int(key_l1)
        for key_l2 in kp_data[key_l1].keys():
            hour = int(key_l2)
            Kp = kp_data[key_l1][key_l2]
            # print (Kp, type(Kp))
            # input()
            # continue
            
            # kp这1天的值不全，导致kp的值是''，入库报错，需要提出空值
            if(''==Kp):
                continue
            if -1==int(Kp):
                continue
  
            ##每个Kp值计算1个等级level
            level,descrip=geomag_strom(int(Kp))
            ##记录时间为结束时间，如果0点，3点，6点，9点，12点，15点，18点，21点，更改为推迟3小时的时间点，3点，6点，9点，12点，15点，18点，21点，24点既为第2天的0点
            delta_hour = datetime.timedelta(hours=3)
            time_str = (datetime.datetime(year,month,day,hour) + delta_hour).strftime('%Y-%m-%d %H:%M:%S')
            
            # 剔除未来时刻的缺省值
            if  datetime.datetime.strptime(time_str,'%Y-%m-%d %H:%M:%S') > datetime.datetime.utcnow():
                continue               
            
            
            debug=0
            #每条记录是1个完整的数据库记录
            #dicts[time_str] = data
            dicts[time_str]['Kp'] = int(Kp)
            dicts[time_str]['level'] = level
            dicts[time_str]['descrip'] = descrip            
            dicts[time_str]['website'] = 'GFZ'
            dicts[time_str]['category_abbr_en'] = 'GFZ_Kp_web'
            
    return dicts

    

def merge_ap_dicts(date_str,ap_data):
    #dicts={}
    dicts = defaultdict(dict)
    ####
    ####March 15, 2020
    datetime_format = datetime.datetime.strptime(date_str, '%B %d, %Y')

    year = datetime_format.year
    month = datetime_format.month

    # # 取年
    # print(datetime_format.year)
    # # 取月
    # print(datetime_format.month)
    for key_l1 in ap_data.keys():
        day = int(key_l1)
        data = ap_data[key_l1]
        time_str = datetime.datetime(year,month,day).strftime('%Y-%m-%d %H:%M:%S')
        debug=0
        ##ap这1天的值不全，导致ap的值是''，入库报错，需要提出空
        if(''==data):
            continue
            
        dicts[time_str]['Ap'] = data
        dicts[time_str]['website'] = 'GFZ'
        dicts[time_str]['category_abbr_en'] = 'GFZ_Kp_web'
    return dicts
    

def read_data(html_file):
    print(__file__,os.path.dirname(os.path.abspath(__file__)))
    # parser = HtmlParser()
    # print('HtmlParser......')

    # html_file1 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\index.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test1.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test2.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test5.html'
    # html_file1 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\qlyymm.html'
    # html_file1 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\qlyymm202003.html'
    # html_file1 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\test\\test_htmlparser\\qlyymm.html'
    
    
    
    
    if not os.path.exists(html_file):
        print(html_file + ' do not exist')
        err = '%s do not exist.'% html_file
        raise Exception(err)
    # if not os.path.exists(html_file2):
    #     print(html_file2 + ' do not exist')
    #     return
    # content = read_file(html_file)
    # print(content)

    soup = BeautifulSoup(open(html_file))
    # 查找标签名为p，class属性为"title"
    # kp_ap_data = soup.find_all("pre", "data")
    tags_small = soup.small
    small_contents = tags_small.contents[0]
    ####正则表达式，提取英文格式的日期
    pattern = re.compile(r"""
        [a-z]+  # at least one+ ascii letters (ignore case is use)
        \s      # one space after
        \d\d?   # one or two digits
        ,?      # an oprtional comma
        \s      # one space after
        \d{4}   # four digits (year)
    """, re.IGNORECASE | re.VERBOSE)

    date_str = pattern.search(small_contents).group()


    # tags_tr = soup.tr
    # tr_contents = tags_tr.contents

    ####新的html，有tbody，旧的只到table
    
    #tags_tbody = soup.body.center.table.tbody##手动下载html格式，有tbody标签
    tags_table = soup.body.center.table##程序自动下载html格式，没有tbody标签
    
    # t2 = soup.center.table.tr

    ####输出table标签的所有子节点
    kp_data = defaultdict(dict)
    ap_data = {}
    for index_level1, tags_level1 in enumerate(tags_table.contents):
        ####根据实际情况，从第9行,第8行，需要根据实际的html定位，开始是kp指数
        ####每隔3个小时更新1个值，按整点取，1天8个值
        ####如果tags_level2是\n跳过
        if ('\n' == tags_level1):
            continue
        if index_level1 < 8:
            continue

        ####总共12列，第1列天，第2列-第9列是1天的8个值，每个值间隔3小时，从00：00：00开始，第10列sum，第11列ap，第12列cp
        for index_level2, tags_level2 in enumerate(tags_level1):
            #print('index_level1,index_level2 = %d %d'%(index_level1,index_level2))
            #### datas_level1 = tags_level2
                ##第3级，第1个值的下1级是当月的第几天day
            if 0 == index_level2:
                for index_level3, tags_level3 in enumerate(tags_level2):
                    #print(index_level2,tags_level3)
                    #day = int(tags_level3.contents[0])  # 字符串换算成int类型整数
                    day = tags_level3.contents[0].zfill(2)
                    ##补2位，前面如果是空格，空格默认占1位
                    # 字符串换算成int类型整数
                    #print(day)
                    debug = 0
            ####
            elif 10 == index_level2:
                # pass
                #print(index_level2, tags_level2)
                ap_data[day] = tags_level2.get_text()
            ####第9是sum值
            elif 1 <= index_level2 and index_level2 <= 8:
                #print(index_level2,tags_level2)
                hour = '%02d'%((index_level2-1) * 3)  # 每隔3小时
                try:
                    #kp_data[day][hour] = tags_level2.get_text()
                    str = tags_level2.get_text()
                    #strr = tags_level2.text
                    kp_data[day][hour] = str[0:1]
                    debug=0
                    #print(kp_data)
                except Exception as e:
                    print(e)

    debug = 0

    data_kp_dicts = merge_kp_dicts(date_str,kp_data)
    data_ap_dicts = merge_ap_dicts(date_str,ap_data)
    
    print(data_kp_dicts)
    print(data_ap_dicts)
    
    return data_kp_dicts,data_ap_dicts



if __name__ == '__main__':
    fullfilepath = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\qlyymm202003.html'

    fullfilepath ='qlyymm_20200318_220000.html'
    read_data(fullfilepath)
    # main2()
    debug = 0
