#!/bin/bash

##配置crontab命令：
#1. crontab -e
#2. * * * * * sh /home/YJY015/code/daemon.sh
#3. wq
#4. crontab -l

##测试crontab命令：
#1. 杀死automatically_task.py进程及其子进程
#2. 查看是否杀死，ps -ef |grep automatically_task.py
#2. 等待1分钟
#3. 查看系统中automatically_task.py进程是否启动，ps -ef |grep automatically_task.py




##配置方法：crontab -e编辑，wq保存
##最小1分钟检查1次，保证最小任务有1分钟生产一次的
##crontab配置调用的shell脚本，带sh命名执行，保证有可执行权限
##配置格式如下
# .---------------- minute (0 - 59)

# |  .------------- hour (0 - 23)

# |  |  .---------- day of month (1 - 31)

# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...

# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat

# |  |  |  |  |

# *  *  *  *  * user-name  command to be executed




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


PROC_NAME='automatically_task.py'
ProNumber=`ps -ef|grep -w $PROC_NAME|grep -v grep|wc -l`
if [ $ProNumber -le 0 ];then
    result=0
else
    result=1
fi
echo "the proc num is :" ${result}

if [ "$result" -eq 1 ] ;then
    echo "the proc is running, no need run it"
    exit 1;
fi


if [ "$result" -eq 0 ] ;then
    echo "the proc is not running, run it now"
    ipcs -q |awk 'NR>3 {print "ipcrm -q", $2}'|sh
    ##重启调度任务
    #sh /home/YJY015/code/refresh_task.sh
    sh $rootpath/code/restart_task.sh
    exit 1;
fi


