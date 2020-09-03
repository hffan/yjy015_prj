# -*- coding: UTF-8 -*-
# from html_parser import *

from bs4 import BeautifulSoup
import os
from collections import defaultdict
import re
import datetime
import bs4




def merge_dst_dicts(date_str, dst_data):
    
    #dicts = {}
    dicts = defaultdict(dict)##字典嵌套赋值需要定义
    ####
    ####March 15, 2020
    datetime_format = datetime.datetime.strptime(date_str, '%B   %Y') ####需要空3个空格

    year = datetime_format.year
    month = datetime_format.month

    # # 取年
    # print(datetime_format.year)
    # # 取月
    # print(datetime_format.month)
    for key_l1 in dst_data.keys():
        day = int(key_l1)#天
        for key_l2 in dst_data[key_l1].keys():
            hour = int(key_l2)#小时
            data = dst_data[key_l1][key_l2]
            time_str = datetime.datetime(year, month, day, hour).strftime('%Y-%m-%d %H:%M:%S')
            debug = 0
            
            #dicts[time_str] = data
            dicts[time_str]['Dst'] = data
            dicts[time_str]['website'] = 'KYOTO'
            dicts[time_str]['category_abbr_en'] = 'KYOTO_Dst_web'
            
    return dicts


def read_data(html_file):
    # parser = HtmlParser()
    # print('HtmlParser......')

    #html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\index.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test1.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test2.html'
    # html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\test5.html'
    # html_file2 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\qlyymm.html'
    # html_file1 = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\test\\test_htmlparser\\qlyymm.html'
    # if not os.path.exists(html_file1):
    #     print(html_file1 + ' do not exist')
    #     return
    if not os.path.exists(html_file):
        print(html_file + ' do not exist')
        ##return
        err = '%s do not exist.'% html_file
        raise Exception(err)
    # content = read_file(html_file)
    # print(content)

    soup = BeautifulSoup(open(html_file))
    # 查找标签名为p，class属性为"title"
    # kp_ap_data = soup.find_all("pre", "data")

    # tags_pre = soup.pre
    # kp_ap_contents = tags_pre.contents

    tags_pre = soup.pre
    pre_contents = tags_pre.contents

    for index_level1, tags_level1 in enumerate(pre_contents):
        ####根据实际情况，从第9行,第8行，需要根据实际的html定位，开始是kp指数
        ####每隔3个小时更新1个值，按整点取，1天8个值
        ####如果tags_level2是\n跳过
        print(type(tags_level1))
        ####如果是回车符，需要返回
        if ('\n' == tags_level1):
            continue
        ####如果是注释，需要返回
        if type(tags_level1)==bs4.element.Comment:
            continue
        debug=0
        data_str = tags_level1.split('\n')


    ####默认第4行包含英文日期
    time_str = data_str[3]
    ####正则表达式，提取英文格式的日期
    pattern = re.compile(r"""
        [a-z]+  # at least one+ ascii letters (ignore case is use)
        \s\s\s      # one space after ,3个空格
        \d{4}   # four digits (year)
    """, re.IGNORECASE | re.VERBOSE)
    ####提取日期
    date_str = pattern.search(time_str).group()


    ####提取物理要素
    dst_data = defaultdict(dict)
    for index,value in enumerate(data_str):
        ####从第8行开始是物理要素
        if index < 7:
            continue
        lines = value.split()
        for index,line in enumerate(lines):
            if 0==index:
                day = int(line)  ## 第1列是天
            else:
                #### 29999999999999999999999999999，1999999999999999999999999，99999999999999999999999999999999各种情况都有
                #### 考虑特大地磁暴，取+999，-99999，判断字符串的长度 len(-99999) = 6,大于6就非法值
                #### if '99999999999999999999999999999999' == line:
                #### 以下判断，or条件，第1个不满足，后面的or条件不执行，如果第1个满足，还执行第2个or条件，会出错
                #### 比如99999999999999999999999999999999在转int类型，超出了int的范围
                #if len(line) > 6 or int(line) < -99999 or int(line) > 999:
                if len(line) > 6 or int(line) < -9999 or int(line) > 999:                
                    break
                hour = (index-1)*1
                data = int(line)
                dst_data[day][hour] = data

        debug=0



    data_dst_dicts = merge_dst_dicts(date_str, dst_data)
    print(data_dst_dicts)
    #input()
    ####解析

    debug = 0
    # parser.feed(content)
    # parser.handle_starttag('pre')
    # print(parser.dst_data)

    # print(type(parser.data))
    # parser.close()

    #### 解析html特定标签内的内容
    # dicts = read_kp(parser.kp_ap_data)
    # dicts = read_ap(parser.kp_ap_data)
    # dicts = read_ap(parser.dst_data)
    # dicts = read_kp(kp_ap_contents)
    # dicts = read_ap(kp_ap_data)

    # small_contents
    # dst_data = 0
    # dicts = read_dst(dst_data)

    return data_dst_dicts


if __name__ == '__main__':
    # main1()
    html_file = 'C:\\Users\\Administrator\\Desktop\\YJY015_centos7.6\\demo\\test_beautifulsoup\\index.html'
    read_data(html_file)
    debug = 0
