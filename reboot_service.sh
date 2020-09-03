#!/bin/sh

############################################################################################################

# 重启网络，需要配置  vim /etc/sysconfig/network-scripts/ifcfg-eno1
# 从linux界面，配置wifi的IP即可，每次重启电脑，IP固定

# TYPE=Ethernet
# PROXY_METHOD=none
# BROWSER_ONLY=no
# BOOTPROTO=none
# DEFROUTE=yes
# IPV4_FAILURE_FATAL=yes
# IPV6INIT=yes
# IPV6_AUTOCONF=yes
# IPV6_DEFROUTE=yes
# IPV6_FAILURE_FATAL=no
# IPV6_ADDR_GEN_MODE=stable-privacy
# NAME=eno1
# UUID=d6b92631-9248-405f-8c4b-21e61d9a0232
# DEVICE=eno1
# ONBOOT=yes
# IPADDR=192.168.1.28
# PREFIX=24
# GATEWAY=192.168.1.1
# DNS=114.114.114.114


# 0. 
# vim /etc/rc.d/rc.local 
# cd /home/redhat/home/YJY015/code;sh reboot_service.sh
# chmod a+x /etc/rc.d/rc.local
#
# 1. 开机重启2个tomcat
# 2. 开机重启automatically_task.py
# 3. 开机启动项shell脚本,调用python，需要使用解释器的全路径，否则python环境变量没有生效，调用失败
# 4. 内网机,不需要启动apsheduler下载任务,需要做判断处理
############################################################################################################


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


##内网路径
#rootpath=/home/redhat/home/YJY015/
##外网路径
#rootpath=/home/YJY015/


##python环境
python_path=/root/anaconda3/bin/python

##重启网络
systemctl restart network

##挂载nfs或者磁盘
mount -a 


##查找tomcat任务，杀掉
tomcat_name='tomcat-015-uus'
pid=$(ps x | grep $tomcat_name | grep -v grep | awk '{print $1}')
echo $pid
echo '根据父进程的pid,查询父进程及其子进程......'
if [ -z $pid ]; then
    echo $tomcat_name '没有启动,不需要杀进程.'
else
    echo $tomcat_name '有启动,需要杀掉进程.'
    ##杀死父进程及其所有的子进程
    kill -9 `pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`  
fi
##重启tomcat服务,重启后端
#cd $rootpath/package/tomcat-015-uus/bin;sh startup.sh
cd $rootpath/package/tomcat-015-uus/bin;pwd;chmod 777 catalina.sh;chmod 777 startup.sh;sh startup.sh
##查看启动情况
ps -ef |grep $tomcat_name




##查找tomcat任务，杀掉
tomcat_name='tomcat-015-web'
pid=$(ps x | grep $tomcat_name | grep -v grep | awk '{print $1}')
echo $pid
echo '根据父进程的pid,查询父进程及其子进程......'
if [ -z $pid ]; then
    echo $tomcat_name '没有启动,不需要杀进程.'
else
    echo $tomcat_name '有启动,需要杀掉进程.'
    ##杀死父进程及其所有的子进程
    kill -9 `pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`  
fi
##重启tomcat服务,重启前端
#cd $rootpath/package/tomcat-015-web/bin;sh startup.sh
cd $rootpath/package/tomcat-015-web/bin;pwd;chmod 777 catalina.sh;chmod 777 startup.sh;sh startup.sh
##查看启动情况
ps -ef |grep $tomcat_name



##查找automatically_apsheduler.py任务，杀掉
codepath=$rootpath/code
# echo $codepath
# sleep 1000

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




# echo ''
# echo '准备启动进程' $processname
# ##启动automatically_apsheduler.py任务
# #cd $codepath; nohup python -u $processname >$program_logname 2>&1 &
# #cd $codepath; nohup /root/anaconda3/bin/python -u $processname >$program_logname 2>&1 &
# cd $codepath; nohup $python_path -u $processname >$program_logname 2>&1 &


####外网需要启动调度流程
if [ "$share_disk_open" == "False" ];then
    #rootpath=$rootpath
    #echo '1'
    #echo $rootpath
    echo ''
    echo '准备启动进程' $processname
    ##启动automatically_apsheduler.py任务
    #cd $codepath; nohup python -u $processname >$program_logname 2>&1 &
    #cd $codepath; nohup /root/anaconda3/bin/python -u $processname >$program_logname 2>&1 &
    cd $codepath; nohup $python_path -u $processname >$program_logname 2>&1 &
fi



##查看启动情况
ps -ef |grep $processname



