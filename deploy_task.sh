#!/bin/sh

####################################################################################################
#1. 部署脚本
#2. 后台运行 cd /home/YJY015/code; nohup sh deploy_task.sh >deploy_task.log 2>&1 &
####################################################################################################


####直接将配置信息加载到session的环境变量中
####config.txt必须为linux格式,如果是windows格式,变量末尾有^M,导致字符串比较失败
source ./cfg/config.txt
echo $share_disk_open
echo $share_disk_rootpath
echo $rootpath


if [ "$share_disk_open" == False ];then
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
#rootpath=/home/redhat/home/YJY015
##外网路径
#rootpath=/home/YJY015


# cd $codepath/test_db;
# pwd
# sleep 1000


##查找automatically_apsheduler.py任务，杀掉
# codepath='/home/YJY015/code'
# data='/home/YJY015/data'
# product='/home/YJY015/product'
# alert='/home/YJY015/alert'


codepath=$rootpath/code/
data=$rootpath/data
product=$rootpath/product
alert=$rootpath/alert


processname='automatically_task.py'
program_logname='automatically_task.log'
apscheduler_logname='apscheduler.log'


##查找automatically_apsheduler.py任务，杀掉
pid=$(ps x | grep $processname | grep -v grep | awk '{print $1}')
echo $pid
echo '查询pid父进程及其子进程......'

if [ -z $pid ]; then
#if [ ! -n $pid ]; then
    echo $processname '没有启动,不需要杀进程.'
else
    echo $processname '有启动,需要杀掉进程.'
    ##杀死父进程及其所有的子进程
    kill -9 `pstree -p $pid | awk -F"[()]" '{for(i=0;i<=NF;i++)if($i~/^[0-9]+$/)print $i}'`  
fi


##先测试连接数据库正常与否
cd $codepath/test/test_db; python connect_db.py 
# exit 0


##删除数据库表data_category,  data_file_info,data_monitor,  product_file_info,prodct_monitor,  alert_file_info,alert_monitor,clean_up_monitor
cd $codepath/test/test_db; python delete_data_category_table.py 
cd $codepath/test/test_db; python delete_data_file_info_table.py
cd $codepath/test/test_db; python delete_data_monitor_table.py
cd $codepath/test/test_db; python delete_alert_file_info_table.py
cd $codepath/test/test_db; python delete_alert_monitor_table.py
cd $codepath/test/test_db; python delete_product_monitor_table.py
cd $codepath/test/test_db; python delete_product_file_info_table.py
cd $codepath/test/test_db; python delete_report_file_info_table.py
cd $codepath/test/test_db; python delete_clean_up_monitor_table.py
cd $codepath/test/test_db; python delete_export_monitor_table.py
cd $codepath/test/test_db; python delete_import_monitor_table.py


##删除事件等级配置表
cd $codepath/test/test_db; python delete_event_configuration_table.py


##删除用户组表，用户信息表
cd $codepath/test/test_db; python delete_contact_group_table.py
cd $codepath/test/test_db; python delete_contact_info_table.py


##删除要素提取表
cd $codepath/test/test_db; python delete_element_f107_table.py
cd $codepath/test/test_db; python delete_element_ace_ep_table.py
cd $codepath/test/test_db; python delete_element_ace_sis_table.py
cd $codepath/test/test_db; python delete_element_ace_sw_table.py
cd $codepath/test/test_db; python delete_element_ace_mag_table.py
cd $codepath/test/test_db; python delete_element_ap_table.py
cd $codepath/test/test_db; python delete_element_dst_table.py
cd $codepath/test/test_db; python delete_element_goes_mag_table.py
cd $codepath/test/test_db; python delete_element_goes_ie_table.py
cd $codepath/test/test_db; python delete_element_goes_ip_table.py
cd $codepath/test/test_db; python delete_element_goes_xr_table.py
cd $codepath/test/test_db; python delete_element_hpi_table.py
cd $codepath/test/test_db; python delete_element_kp_table.py
cd $codepath/test/test_db; python delete_element_rad_table.py
cd $codepath/test/test_db; python delete_element_ssn_table.py
cd $codepath/test/test_db; python delete_element_ste_het_table.py
cd $codepath/test/test_db; python delete_element_ste_sw_table.py
cd $codepath/test/test_db; python delete_element_ste_mag_table.py
cd $codepath/test/test_db; python delete_element_swpc_flare_table.py
cd $codepath/test/test_db; python delete_element_tec_table.py


##删除本地数据/home/YJY015/data
cd $data; rm -rf $data
cd $product; rm -rf $product
cd $alert; rm -rf $alert


##删除本地log日志$codepath/logger/log/2020-05-20
logtime=$(date "+%Y-%m-%d")
echo $logtime
#cd $codepath/logger/log/2020-05-20; rm -rf $codepath/logger/log/2020-05-20
cd $codepath/logger/log/$logtime; rm -rf $codepath/logger/log/$logtime


##删除调度log日志 $codepath/apscheduler.log;  $codepath/automatically_apsheduler.log
rm -f  $codepath/$apscheduler_logname;
rm -f  $codepath/$program_logname;


##新建数据库
cd $codepath/test/test_db; python create_yjy015_db.py


##新建data_category,  data_file_info,data_monitor,  product_file_info,prodct_monitor,  alert_file_info,alert_monitor,clean_up_monitor
cd $codepath/test/test_db; python create_data_category_table.py
cd $codepath/test/test_db; python create_data_file_info_table.py
cd $codepath/test/test_db; python create_data_monitor_table.py
cd $codepath/test/test_db; python create_product_file_info_table.py
cd $codepath/test/test_db; python create_product_monitor_table.py
cd $codepath/test/test_db; python create_alert_file_info_table.py
cd $codepath/test/test_db; python create_alert_monitor_table.py
cd $codepath/test/test_db; python create_report_file_info_table.py
cd $codepath/test/test_db; python create_clean_up_monitor_table.py
cd $codepath/test/test_db; python create_export_monitor_table.py
cd $codepath/test/test_db; python create_import_monitor_table.py


##新建事件等级配置表
cd $codepath/test/test_db; python create_event_configuration_table.py


##创建用户组表，创建用户信息表
cd $codepath/test/test_db; python create_contact_group_table.py
cd $codepath/test/test_db; python create_contact_info_table.py


##创建要素提取表
cd $codepath/test/test_db; python create_element_ace_ep_table.py
cd $codepath/test/test_db; python create_element_ace_sis_table.py
cd $codepath/test/test_db; python create_element_ace_sw_table.py
cd $codepath/test/test_db; python create_element_ace_mag_table.py
cd $codepath/test/test_db; python create_element_ap_table.py
cd $codepath/test/test_db; python create_element_dst_table.py
cd $codepath/test/test_db; python create_element_f107_table.py
cd $codepath/test/test_db; python create_element_goes_mag_table.py
cd $codepath/test/test_db; python create_element_goes_ie_table.py
cd $codepath/test/test_db; python create_element_goes_ip_table.py
cd $codepath/test/test_db; python create_element_goes_xr_table.py
cd $codepath/test/test_db; python create_element_hpi_table.py
cd $codepath/test/test_db; python create_element_kp_table.py
cd $codepath/test/test_db; python create_element_rad_table.py
cd $codepath/test/test_db; python create_element_ssn_table.py
cd $codepath/test/test_db; python create_element_ste_het_table.py
cd $codepath/test/test_db; python create_element_ste_sw_table.py
cd $codepath/test/test_db; python create_element_ste_mag_table.py
cd $codepath/test/test_db; python create_element_swpc_flare_table.py
cd $codepath/test/test_db; python create_element_tec_table.py


##插入表data_category
cd $codepath/test/test_db; python insert_data_category_table.py
cd $codepath/test/test_db; python insert_contact_group_table.py 
cd $codepath/test/test_db; python insert_contact_info_table.py
cd $codepath/test/test_db; python insert_event_configuration_table.py


# echo '请先确认,是否需要手动修改data_category配置表?'
# read -s -n1 -p "[ Press any key to continue ... ] "


echo ''
echo '准备启动进程' $processname

##启动automatically_apsheduler.py任务
cd $codepath; nohup python -u $processname >$program_logname 2>&1 &
ps -ef |grep $processname


##插入历史数据20年
echo 'nohup python insert_element_f107_table.py>/dev/null 2>&1 &'
echo '后台插入,element_f107......'
cd $codepath/test/test_db; nohup python insert_element_f107_table.py>/dev/null 2>&1 &

echo 'nohup python insert_element_ssn_table.py>/dev/null 2>&1 &'
echo '后台插入,element_ssn......'
cd $codepath/test/test_db; nohup python insert_element_ssn_table.py>/dev/null 2>&1 &


##太耗时,临时注释掉，真实环境种，部署需要人机交互确认是否打开
# while true
# do
    # read -r -p "Are You Sure? [YES,yes,Y,y / NO,no,N,n] " input

    # case $input in
        # [yY][eE][sS]|[yY])
            # echo "Yes"
            # cd /home/YJY015/code/test_db; python insert_element_f107_table.py 
            # cd /home/YJY015/code/test_db; python insert_element_ssn_table.py            
            # exit 1
            # ;;

        # [nN][oO]|[nN])
            # echo "No"
            # exit 1	       	
            # ;;

        # *)
            # echo "Invalid input..."
            # ;;
    # esac
# done



