#!/bin/sh

########################################################################################################################
#1.更新event_configurationy表: 删除表event_configurationy，新建表event_configurationy,插入表event_configurationy
########################################################################################################################

####直接将配置信息加载到session的环境变量中
####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
source ./cfg/config.txt
echo $share_disk_open
echo $share_disk_rootpath
echo $rootpath


if [ "$share_disk_open" == "False" ];then
    rootpath=$rootpath
    #echo '1'
    echo $rootpath
fi

if [ "$share_disk_open" == "True" ];then
    rootpath=$share_disk_rootpath$rootpath
    #echo '2'    
    echo $rootpath    
fi


##内网
#rootpath=/home/redhat/home/YJY015

##外网
#rootpath=/home/YJY015



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




