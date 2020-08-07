#!/bin/sh

########################################################################################################################
#1.更新event_configurationy表: 删除表data_category，新建表data_category,插入表data_category
########################################################################################################################

##外网
rootpath=/home/YJY015
##内网
#rootpath=/home/redhat/home/YJY015


##python环境
python_path=/root/anaconda3/bin/python


codepath=$rootpath/code
##删除数据库表event_configurationy
cd $codepath/test/test_db/; 
#cd $codepath; 
$python_path $codepath/test/test_db/delete_event_configuration_table.py 

##新建event_configurationy
cd $codepath/test/test_db/; 
#cd $codepath; 
$python_path $codepath/test/test_db/create_event_configuration_table.py

##插入表event_configurationy
cd $codepath/test/test_db/; 
#cd $codepath; 
$python_path $codepath/test/test_db/insert_event_configuration_table.py




