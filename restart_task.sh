#!/bin/sh

##############################################################################
# 1. 查找父进程及其子进程
# 2. 杀掉父进程及其子进程
# 3. 重启进程
# 4. 前端如果修改了数据库配置表,需要调用此脚本,进而更新任务读取的配置参数
# 5. 前端界面，需要调用此脚本，每次更新，新增下载配置，需要重启此任务
##############################################################################


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
#codepath='/home/redhat/home/YJY015/code'
##外网
#codepath='/home/YJY015/code'


##python环境
python_path=/root/anaconda3/bin/python



##查找automatically_apsheduler.py任务，杀掉
#codepath='/home/YJY015/code'
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


echo ''
echo '准备启动进程' $processname


##启动automatically_apsheduler.py任务
#cd $codepath; nohup python -u $processname >$program_logname 2>&1 &
#cd $codepath; nohup $python_path -u $processname >$program_logname 2>&1 &
cd $rootpath/code; nohup $python_path -u $processname >$program_logname 2>&1 &
ps -ef |grep $processname





