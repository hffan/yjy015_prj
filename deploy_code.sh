#!/bin/sh


########################################################################################################################
#1. 针对内网服务器,部署脚本，只部署代码，不启动任务
#2. 只部署代码和数据库,不启动数据收集任务，不启动要素提取任务，不启动产品生产任务，不启动警报提取业务和发送警报短信
#3. 需要删除表，重新创建，重新插入，表数据类型float4更改为float8; 表log日志由255更改为4096
########################################################################################################################


##外网路径
rootpath=/home/YJY015/code/
##内网路径
rootpath=/home/redhat/home/YJY015/code/




##先测试连接数据库正常与否
cd $rootpath/test/test_db; python connect_db.py 
# exit 0


##删除数据库表data_category,  data_file_info,data_monitor,  product_file_info,prodct_monitor,  alert_file_info,alert_monitor,report_file_info
cd $rootpath/test/test_db; python delete_data_category_table.py 
cd $rootpath/test/test_db; python delete_data_file_info_table.py
cd $rootpath/test/test_db; python delete_data_monitor_table.py
cd $rootpath/test/test_db; python delete_alert_file_info_table.py
cd $rootpath/test/test_db; python delete_alert_monitor_table.py
cd $rootpath/test/test_db; python delete_product_monitor_table.py
cd $rootpath/test/test_db; python delete_product_file_info_table.py
cd $rootpath/test/test_db; python delete_report_file_info_table.py
cd $rootpath/test/test_db; python delete_clean_up_monitor_table.py
cd $rootpath/test/test_db; python delete_export_monitor_table.py
cd $rootpath/test/test_db; python delete_import_monitor_table.py


##删除事件等级配置表
cd $rootpath/test/test_db; python delete_event_configuration_table.py


##删除用户组表，用户信息表
cd $rootpath/test/test_db; python delete_contact_group_table.py
cd $rootpath/test/test_db; python delete_contact_info_table.py


##删除要素提取表
cd $rootpath/test/test_db; python delete_element_f107_table.py
cd $rootpath/test/test_db; python delete_element_ace_ep_table.py
cd $rootpath/test/test_db; python delete_element_ace_sis_table.py
cd $rootpath/test/test_db; python delete_element_ace_sw_table.py
cd $rootpath/test/test_db; python delete_element_ace_mag_table.py
cd $rootpath/test/test_db; python delete_element_ap_table.py
cd $rootpath/test/test_db; python delete_element_dst_table.py
cd $rootpath/test/test_db; python delete_element_goes_mag_table.py
cd $rootpath/test/test_db; python delete_element_goes_ie_table.py
cd $rootpath/test/test_db; python delete_element_goes_ip_table.py
cd $rootpath/test/test_db; python delete_element_goes_xr_table.py
cd $rootpath/test/test_db; python delete_element_hpi_table.py
cd $rootpath/test/test_db; python delete_element_kp_table.py
cd $rootpath/test/test_db; python delete_element_rad_table.py
cd $rootpath/test/test_db; python delete_element_ssn_table.py
cd $rootpath/test/test_db; python delete_element_ste_het_table.py
cd $rootpath/test/test_db; python delete_element_ste_sw_table.py
cd $rootpath/test/test_db; python delete_element_ste_mag_table.py
cd $rootpath/test/test_db; python delete_element_swpc_flare_table.py
cd $rootpath/test/test_db; python delete_element_tec_table.py


##新建数据库
cd $rootpath/test/test_db; python create_yjy015_db.py


##新建data_category,  data_file_info,data_monitor,  product_file_info,prodct_monitor,  alert_file_info,alert_monitor,  report_file_info
cd $rootpath/test/test_db; python create_data_category_table.py
cd $rootpath/test/test_db; python create_data_file_info_table.py
cd $rootpath/test/test_db; python create_data_monitor_table.py
cd $rootpath/test/test_db; python create_product_file_info_table.py
cd $rootpath/test/test_db; python create_product_monitor_table.py
cd $rootpath/test/test_db; python create_alert_file_info_table.py
cd $rootpath/test/test_db; python create_alert_monitor_table.py
cd $rootpath/test/test_db; python create_report_file_info_table.py
cd $rootpath/test/test_db; python create_clean_up_monitor_table.py
cd $rootpath/test/test_db; python create_export_monitor_table.py
cd $rootpath/test/test_db; python create_import_monitor_table.py

##新建事件等级配置表
cd $rootpath/test/test_db; python create_event_configuration_table.py


##创建用户组表，创建用户信息表
cd $rootpath/test/test_db; python create_contact_group_table.py
cd $rootpath/test/test_db; python create_contact_info_table.py


##创建要素提取表
cd $rootpath/test/test_db; python create_element_ace_ep_table.py
cd $rootpath/test/test_db; python create_element_ace_sis_table.py
cd $rootpath/test/test_db; python create_element_ace_sw_table.py
cd $rootpath/test/test_db; python create_element_ace_mag_table.py
cd $rootpath/test/test_db; python create_element_ap_table.py
cd $rootpath/test/test_db; python create_element_dst_table.py
cd $rootpath/test/test_db; python create_element_f107_table.py
cd $rootpath/test/test_db; python create_element_goes_mag_table.py
cd $rootpath/test/test_db; python create_element_goes_ie_table.py
cd $rootpath/test/test_db; python create_element_goes_ip_table.py
cd $rootpath/test/test_db; python create_element_goes_xr_table.py
cd $rootpath/test/test_db; python create_element_hpi_table.py
cd $rootpath/test/test_db; python create_element_kp_table.py
cd $rootpath/test/test_db; python create_element_rad_table.py
cd $rootpath/test/test_db; python create_element_ssn_table.py
cd $rootpath/test/test_db; python create_element_ste_het_table.py
cd $rootpath/test/test_db; python create_element_ste_sw_table.py
cd $rootpath/test/test_db; python create_element_ste_mag_table.py
cd $rootpath/test/test_db; python create_element_swpc_flare_table.py
cd $rootpath/test/test_db; python create_element_tec_table.py


##插入表data_category
cd $rootpath/test/test_db; python insert_data_category_table.py
cd $rootpath/test/test_db; python insert_contact_group_table.py 
cd $rootpath/test/test_db; python insert_contact_info_table.py
cd $rootpath/test/test_db; python insert_event_configuration_table.py


##插入历史数据20年
echo 'nohup python insert_element_f107_table.py>/dev/null 2>&1 &'
echo '后台插入,element_f107......'
cd $rootpath/test/test_db; nohup python insert_element_f107_table.py>/dev/null 2>&1 &

echo 'nohup python insert_element_ssn_table.py>/dev/null 2>&1 &'
echo '后台插入,element_ssn......'
cd $rootpath/test/test_db; nohup python insert_element_ssn_table.py>/dev/null 2>&1 &




