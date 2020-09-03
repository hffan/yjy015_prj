# -*- coding: utf-8 -*-


"""
@user guide
2020-07-24 15:44:51 
                    1. 外网IP： 192.168.1.28
                    2. 内网IP:
                                66.32.130.134
                                66.32.130.136
                                66.32.130.137
                                66.32.130.138
                    3. 笔记本虚拟机：192.168.1.11
                    4. code只需要部署到66.32.130.137，66.32.130.138上可以访问
                    5. 外网客户端IP：192.168.1.26



@modify history
2020-05-29 09:52:51                
                    1. dataroot_path: UI界面，通过tomcat发布路径，除/根路径访问不了，/home或者其他/xx目录，都可以发布
                    2. 部署的时候，确保dataroot_path存在，而且需要配置tomcat里的路径，配置完tomcat里的文件，需要重启tomcat
                    3. data_category表里配置的路径，都是相对路径                
2020-05-29 09:53:14
                    1. 添加字体库引用
2020-05-29 13:38:11
                    1. 本地测试，需要更改yjy015名称，数据目录data，产品目录product,
2020-05-29 20:22:26
                    1. 4类警报事件，默认都放alert文件夹下，不创建下一级文件夹，创建下一级文件夹，导致alert文件夹名称不好截取
2020-06-01 10:32:31
                    1. conf配置文件，尽量配置参数，路径放到代码里拼接，conf文件如果拼接好路径，代码里路径还需要拆分，因为数据库中path路径中多带了文件夹名称，比如data,product,alert
2020-07-09 17:50:55
                    1. 增加导入，导出功能的根路径参数定义
2020-07-24 15:59:55
                    1. 每次部署需要更改share_disk_open,host      
2020-07-24 17:19:55
                    1. 目前使用nfs，把66.32.130.137共享给66.32.130.138，/home/redhat/文件夹不能删除，不能更改名称
                    2. root,abc1234
                    3. 66.32.130.137节点如下
                    (base) [root@localhost ~]# lsblk
NAME                  MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda                     8:0    0  1.1T  0 disk 
├─sda1                  8:1    0  200M  0 part /boot/efi
├─sda2                  8:2    0    1G  0 part /boot
└─sda3                  8:3    0  1.1T  0 part 
  ├─centos-root       253:0    0   50G  0 lvm  /
  └─centos-swap       253:1    0 31.3G  0 lvm  [SWAP]
sdb                     8:16   0  4.3T  0 disk 
└─vg_redhat-lv_redhat 253:2    0  4.3T  0 lvm  /home/redhat

                    4. 66.32.130.138节点如下
(base) [root@localhost ~]# lsblk
NAME            MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda               8:0    0  1.1T  0 disk 
├─sda1            8:1    0  200M  0 part /boot/efi
├─sda2            8:2    0    1G  0 part /boot
└─sda3            8:3    0  1.1T  0 part 
  ├─centos-root 253:0    0   50G  0 lvm  /
  └─centos-swap 253:1    0 31.3G  0 lvm  [SWAP]    

(base) [root@localhost ~]# df -h
文件系统                    容量  已用  可用 已用% 挂载点
devtmpfs                     63G     0   63G    0% /dev
tmpfs                        63G  8.0K   63G    1% /dev/shm
tmpfs                        63G   12M   63G    1% /run
tmpfs                        63G     0   63G    0% /sys/fs/cgroup
/dev/mapper/centos-root      50G   13G   37G   26% /
/dev/sda2                  1021M  169M  853M   17% /boot
/dev/sda1                   200M   12M  189M    6% /boot/efi
66.32.130.137:/home/redhat  4.3T  264M  4.3T    1% /home/redhat
tmpfs                        13G     0   13G    0% /run/user/1001
tmpfs                        13G  4.0K   13G    1% /run/user/42
tmpfs                        13G   20K   13G    1% /run/user/0

  
2020-08-04 02:17:30
                    1. 新增log日志配置路径
2020-08-20 09:49:03
                    1. alert路径，统一更改为report，alert路径作废
                    

                                        
"""


share_disk_open             = 'False'                   ##True就是内网机，False是外网机或者公司网络
#host = '66.32.130.137'                                 ##内网服务器1，IP 
#host = '66.32.130.138'                                 ##内网服务器2，IP 
#host = '192.168.1.28'                                  ##外网IP
host = '192.168.1.135'                                  ##公司IP，55节点
#host = '192.168.1.145'                                 ##公司IP，78节点
#host = '192.168.1.11'                                  ##WIFI,笔记本虚拟机IP
#host = '10.1.6.104'                                    ##公司网线,笔记本虚拟机IP



share_disk_rootpath         = '/home/redhat/'        ##内网机共享磁盘路径，数据导入功能，解压需要此根路径
rootpath        = '/home/YJY015/'
dataname        = 'data'
productname     = 'product'
#alertname       = 'alert'
alertname       = 'report'
db_name                     = 'yjy015'
download_name               = 'download.py'
import_name                 = 'import'
export_name                 = 'export'

####兼容外网,内网路径
if 'True' == share_disk_open:
    rootpath = share_disk_rootpath + rootpath
if 'False' == share_disk_open:
    rootpath = rootpath 
# print (rootpath)
# input()

configs = {
           'db_name':db_name,
           # 'data_rootpath':         rootpath + '/' + dataname + '/',
           # 'product_rootpath':      rootpath + '/' + productname + '/',
           # 'alert_geomag_storm_path':   rootpath + '/' + alertname + '/',
           # 'alert_electron_burst_path': rootpath + '/' + alertname + '/',
           # 'alert_solar_flare_path':    rootpath + '/' + alertname + '/',
           # 'alert_solar_proton_path':   rootpath + '/' + alertname + '/',
           'rootpath':         rootpath + '/',
           'dataname':         dataname,
           'productname':      productname,
           'alertname':         alertname,
           'exe_fullpath':    rootpath + '/code/' + download_name,
           'import_rootpath':   rootpath + import_name + '/',
           'export_rootpath':   rootpath + export_name + '/',
           'log_rootpath': rootpath + '/log/',
           #'import_json_rootpath':   rootpath + 'json' + '/' + import_name + '/',
           #'export_json_rootpath':   rootpath + 'json' + '/' + export_name + '/',
           'export_json_rootpath':   rootpath + 'json' + '/',
           'share_disk_open':share_disk_open,
           'share_disk_rootpath':share_disk_rootpath,
           # 'alert_geomag_storm_path':   rootpath + '/' + alertname + '/',
           # 'alert_electron_burst_path': rootpath + '/' + alertname + '/',
           # 'alert_solar_flare_path':    rootpath + '/' + alertname + '/',
           # 'alert_solar_proton_path':   rootpath + '/' + alertname + '/',           
           # 'alert_geomag_storm_path':   rootpath + '/' + alertname + '/geomag_storm/',
           # 'alert_electron_burst_path': rootpath + '/' + alertname + '/electron_burst/',
           # 'alert_solar_flare_path':    rootpath + '/' + alertname + '/solar_flare/',
           # 'alert_solar_proton_path':   rootpath + '/' + alertname + '/solar_proton/',
           'fonts_path':            rootpath + '/code/fonts/SimSun.ttf',
           'formatpath':            rootpath + '/code/element_opt/format.lst',
           'geomag_storm_docx':     rootpath + '/code/event_alert_opt/geomag_storm.docx',
           'electron_burst_docx':   rootpath + '/code/event_alert_opt/electron_burst.docx',
           'solar_flare_docx':      rootpath + '/code/event_alert_opt/solar_flare.docx',
           'solar_proton_docx':     rootpath + '/code/event_alert_opt/solar_proton.docx',           
           #'host':'192.168.1.135', 
           #'host':'192.168.1.145', 
           'host':host,            
           #'host':'66.32.130.137',            
           #'host':'192.168.1.1',            
           'user':'postgres',
           'password':'YJY015_1234.',
           'database':'postgres',
           'port':'5432',
           'table_event_configuration':'event_configuration'}
           
