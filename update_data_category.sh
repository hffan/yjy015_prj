#!/bin/sh

########################################################################################################################
#1.更新data_category表: 先停掉下载任务，删除表data_category，新建表data_category,插入表data_category
########################################################################################################################

##外网
rootpath=/home/YJY015
##内网
#rootpath=/home/redhat/home/YJY015

##python环境
python_path=/root/anaconda3/bin/python



##查找automatically_apsheduler.py任务，杀掉
#codepath='/home/YJY015/code'
codepath=$rootpath/code
processname='automatically_task.py'
program_logname='automatically_task.log'



##查找automatically_apsheduler.py任务，杀掉
pid=$(ps x | grep $processname | grep -v grep | awk '{print $1}')
echo $pid
echo '根据父进程的pid,查询父进程及其子进程......'


if [ -z $pid ]; then
    echo $processname '没有启动,不需要杀进程.'
else
    echo $processname '有启动,需要杀掉进程.'
    ##杀死父进程及其所有的子进程
    kill -9 `pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`  
fi



##删除数据库表data_category
cd $codepath/test/test_db; $python_path delete_data_category_table.py 

##新建data_category
cd $codepath/test/test_db; $python_path create_data_category_table.py

##插入表data_category
cd $codepath/test/test_db; $python_path insert_data_category_table.py




echo ''
echo '准备启动进程' $processname


##启动automatically_apsheduler.py任务
#cd $codepath; nohup python -u $processname >$program_logname 2>&1 &
cd $codepath; nohup $python_path -u $processname >$program_logname 2>&1 &
ps -ef |grep $processname




