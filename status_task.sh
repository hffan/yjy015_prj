#!/bin/sh

##############################################################################
# 1. 查找父进程及其子进程
# 2. 显示父进程及其子进程状态
# 3. 每天UTC=12点,BJT=UTC+8 = 20点,开始清理进程状态是sk_wait_data
##############################################################################


processname='automatically_task.py'
pid=$(ps x | grep $processname | grep -v grep | awk '{print $1}')
echo $pid
echo '根据父进程的pid,查询父进程及其子进程......'


if [ -z $pid ]; then
    echo $processname '没有启动......'
else
    echo $processname '有启动......'
    ##杀死父进程及其所有的子进程
    child_PIDS=`pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`
    echo $child_PIDS
    #echo ${child_PIDS[@]}##打印数组内容
    
    for child_PID in ${child_PIDS[@]}
    do
        #echo $child_PID
        process_status=`cat /proc/$child_PID/wchan`
        #echo $child_PID,$process_status
        if [ 'sk_wait_data' = $process_status ];then
            echo $child_PID,$process_status
            kill -9 $child_PID
        fi
    done
    
fi



