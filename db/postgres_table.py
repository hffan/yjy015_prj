# -*- coding:utf-8 -*-
import os
import sys
import time
import re
import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from cfg.conf import *
from sys_interface.sys_std import *
from sys_interface.sys_str import *


"""
@modify history
2020-05-12 17:52:30
                    1. t_task表合并到data_category表里
                    2. t_task_monitor表合并到数据库file_info_db里
2020-05-22 08:53:18
                    1. 对task_monitor表，新增update_time字段，用于重做任务更新时间
                    2. element_f107表，删除字段 julian float4 not null
                    3. element_goes_xr表，增加level字段
2020-05-26 10:21:31
                    1. 创建product_file_info表
                    2. kp表新增level字段
                    3. ace_mag表新增Bx_GSE，By_GSE，Bz_GSE字段
                    4. goes_ie表里新增IEFday字段,level字段
                    5. goes_ip表里新增Ad，An，level字段
                    6. goes_xr表里新增level,HAF字段
2020-06-23 18:10:45
                    1. 所有单精度24,float4更改为双精度53,float8
                    
2020-07-21 17:22:57
                    1. contact_info中的group_id由integer更改为vachar
                    2. contact_group中的id由serial自增int4更改为vachar
                    
2020-08-06 17:32:20
                    1. alert_file_time表里，utc_time更改为bj_time
                    2. import_monitor表里status更改为int2,1,2,3分别代表失败，导入中，成功
                    3. import_monitor表里增加filesize，类型float8，单位MB
                 
2020-08-08 10:33:20 
                    1. 创建element_info表，前端界面，显示要素提取，显示每天到报率
                    2. 可以为空字段
                       element_name_en varchar(50) null,
                       gain_amount int4 null,
                       arrival_rate varchar(10) null,
                       update_time TIMESTAMP(0) null
                    
2020-08-21 10:20:47
                    1. clean_up_monitor表，status状态由BOOLEAN更改为int2类型,1，2，3，代表失败，删除中，成功。
"""






class PostgresTable:
       
    def __init__(self):
        #####统一配置参数，便于修改
        #self.database = 'postgres'
        #self.host = "192.168.160.129"
        #self.host = "192.168.160.130"
        #self.host = "10.1.100.55"
        #self.user = "postgres"
        #self.password = "123456"
        #self.password = "YJY015_1234."
        #self.port = '5432'
        self.database = configs['database']
        self.host = configs['host']
        self.user = configs['user']
        self.password = configs['password']
        self.port = configs['port']
        return

        
    ####连接数据路
    def connect_db(self, database_name):
        con = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                               port=self.port)
        ##创建游标对象
        f_print('connect %s successful!' % database_name)

        
    # def pg_cmd(self, database_name, cmd):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # cursor.execute(cmd)
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('pg_cmd %s finished!' % cmd)
        
        
    def displayinterprater(self):
        f_print(sys.executable)
 
 
    ##创建数据库
    def create_db(self, database_name):
        con = psycopg2.connect(database=self.database, host=self.host, user=self.user, password=self.password,
                               port=self.port)
        ##创建游标对象
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        ##创建数据库
        try:
            cursor.execute('create database {}'.format(database_name))
        except Exception as e:
            f_print(e)
            # exit()
        f_print('create_db %s successful!' % database_name)
    
    
    ##删除数据库
    def delete_db(self, database_name):
        con = psycopg2.connect(database=self.database, host=self.host, user=self.user, password=self.password,
                               port=self.port)
        ##创建游标对象
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        ##创建数据库
        try:
            cursor.execute('drop database {}'.format(database_name))
        except Exception as e:
            f_print(e)
            # exit()
        f_print('delete_db %s successful!' % database_name)
        
        
        
        
    ##删除数据库中的表
    def delete_table(self,database_name,table_name):
        con = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                               port=self.port)
        ##创建游标对象
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        ##创建数据库
        try:
            cursor.execute('drop table {}'.format(table_name))
        except Exception as e:
            f_print(e)
            # exit()
        f_print('delete_table %s successful!' % table_name)

        
    # def create_datatype_info_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # # serial自动增加
        # try:
            # sqlcmd = '''create table file_info(
                            # id serial not null primary key,
                            # datatype varchar not null,
                            # url varchar(255) not null,
                            # record_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,
                            # band varchar(255) not null,
                            # exp varchar(255) not null,
                            # savepath varchar(255) not null
                            # )'''
            # cursor.execute(sqlcmd)
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_file_info_table finished!')
        
        
        
        
    def create_data_file_info_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 每条大概4000多条记录，需要根据常用的变量创建索引，便于查询
        # 插入时候，使用state，category_id，start_time 建立复合索引
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # file_size单位是byte
        try:
            sqlcmd = '''create table data_file_info(
                            id serial not null primary key,
                            category_id integer not null,
                            category_abbr_en varchar(20) not null,                           
                            filename varchar not null,
                            path varchar(255) not null,
                            record_time TIMESTAMP(0) not null,
                            start_time TIMESTAMP(0) not null,
                            end_time TIMESTAMP(0) not null,
                            file_size integer not null,
                            state BOOLEAN not null,
                            log varchar(255) not null,
                            element_storage_status BOOLEAN not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_data_file_info_table finished!')
    
    
    
    
    ##建立复合索引，入库归档查询校验使用
    def create_data_file_info_Rindex(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 每条大概4000多条记录，需要根据常用的变量创建索引，便于查询
        # 插入时候，使用state，category_id，start_time 建立复合索引
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        try:
            sqlcmd = '''CREATE INDEX "Rindex" ON "data_file_info" USING btree (
                      "category_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
                      "filename" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST,
                      "state" "pg_catalog"."bool_ops" ASC NULLS LAST
                    );'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_data_file_info_index finished!')
        
        
        
        
    ##建立复合索引，用户查询数据，展示使用
    def create_data_file_info_Sindex(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 每条大概4000多条记录，需要根据常用的变量创建索引，便于查询
        # 插入时候，使用state，start_time 建立复合索引
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        try:
            sqlcmd = '''CREATE INDEX "Sindex" ON "data_file_info" USING btree (
                      "category_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
                      "start_time" "pg_catalog"."timestamp_ops" ASC NULLS LAST
                    );'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_data_file_info_index finished!')
        
        
        
        
    def create_data_category_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        try:
            # 外链到website_info表的web_id字段
            # web_id integer not null foreign key reference website_info (web_id),
            # 需要主键 category_id serial not null,
            cursor.execute('''create table data_category(
                            category_id serial not null primary key,                            
                            update_time TIMESTAMP(0) not null,
                            website varchar(255) not null,
                            data_class varchar(255) not null,
                            data_content varchar(255) not null,
                            research_area varchar(255) not null,
                            category_name_zh varchar(255) not null,
                            category_abbr_en varchar(20) not null,
                            url varchar(255) not null,
                            download_filename varchar(255) not null,
                            regular_expression varchar(255) not null,                          
                            save_path varchar(255) not null,
                            save_filename varchar(255) not null,
                            suffix varchar(10) not null,
                            download_priority integer not null, 
                            frequency varchar(255) not null,
                            scheduling_interval_min integer not null, 
                            scheduling_delayed_min integer not null,                             
                            num_collect_perday integer not null, 
                            num_store_perday integer not null,                             
                            file_size float8 not null,
                            daily_increment float8 not null,                             
                            website_status BOOLEAN not null,                            
                            redo_flag BOOLEAN not null,
                            url_date_flag BOOLEAN not null,
                            element_extract_flag BOOLEAN not null,
                            note varchar(255) not null                         
                            )''')
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_data_category_table finished!')
    
    
    
    
    # def create_data_category_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # # 外链到website_info表的web_id字段
            # # web_id integer not null foreign key reference website_info (web_id),
            # cursor.execute('''create table data_category(
                            # category_id serial not null,
                            # update_time TIMESTAMP(0) not null,
                            # category_name_zh varchar(255) not null,
                            # category_abbr_en varchar(20) not null,
                            # website varchar(255) not null,
                            # data_class varchar(255) not null,
                            # research_area varchar(255) not null,
                            # url varchar(255) not null,
                            # band varchar(255) not null,
                            # exp varchar(255) not null,
                            # savepath varchar(255) not null,
                            # cwd varchar(255) not null,
                            # priority integer not null,
                            # num_collect_perday integer not null,
                            # num_store_perday integer not null,
                            # note varchar(255) not null,
                            # redo_flag BOOLEAN not null,
                            # website_status BOOLEAN not null                            
                            # )''')
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_data_category_table finished!')
        
        
        
        
    # def create_data_category_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # # 外链到website_info表的web_id字段
            # # web_id integer not null foreign key reference website_info (web_id),
            # cursor.execute('''create table data_category(
                            # category_id serial not null,
                            # update_time TIMESTAMP(0) not null,
                            # category_name_zh varchar(255) not null,
                            # category_abbr_en varchar(20) not null,
                            # website varchar(255) not null,
                            # data_class varchar(255) not null,
                            # research_area varchar(255) not null,
                            # url varchar(255) not null,
                            # band varchar(255) not null,
                            # exp varchar(255) not null,
                            # savepath varchar(255) not null,
                            # cwd varchar(255) not null,
                            # priority integer not null,
                            # num_perday integer not null,
                            # note varchar(255) not null,
                            # task_triggers varchar(20) not null,
                            # task_hour varchar(128) not null,
                            # task_minute varchar(128) not null,
                            # task_second varchar(128) not null,
                            # redo_flag BOOLEAN not null,
                            # website_status BOOLEAN not null                            
                            # )''')
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_data_category_table finished!')
        
        
        
        
    # def create_website_info_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # cursor.execute('''create table website_info(
                            # web_id serial not null primary key,
                            # record_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,
                            # website varchar(255) not null,
                            # home_link varchar(255) not null,
                            # log varchar(255) not null
                            # )''')
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_website_info_table finished!')

        
    # def create_instrument_info_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # cursor.execute('''create table instrument_info(
                            # intstrument_id serial not null primary key,
                            # record_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,
                            # instrument_name varchar(255) not null,
                            # link varchar(255) not null,
                            # log varchar(255) not null
                            # )''')
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_instrument_info_table finished!')
        
        
    # def create_datatype_info_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:
            # cursor.execute('''create table datatype_info(
                            # datatype varchar(255) not null primary key,
                            # record_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,
                            # savepath varchar(255) not null,
                            # band varchar(255) not null,
                            # exp varchar(255) not null,
                            # url varchar(255) not null
                            # )''')
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_datatype_info_table finished!')

        
    # def create_foreignkey(self, database_name):
        # return 
        

    ##创建f107表
    ##表名统一用小写，避免有兼容冲突问题
    def create_element_f107_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        try:
            sqlcmd = '''create table element_f107(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            carrington float8 not null,
                            obsflux float8 not null,
                            adjflux float8 not null,
                            ursiflux float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_f107_table finished!')
        

    ##创建rad表
    def create_element_rad_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        try:
            sqlcmd = '''create table element_rad(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            station varchar(10) not null,
                            freq int4 not null,
                            flux int4 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_rad_table finished!')


    ##创建ssn表
    def create_element_ssn_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        try:
            sqlcmd = '''create table element_ssn(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            sn int4 not null,
                            std float8 not null,
                            num_obs int4 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ssn_table finished!')


    ##创建swpc_flare表
    def create_element_swpc_flare_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 表名区分大小写
        try:
            sqlcmd = '''create table element_swpc_flare(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            F107 int4 not null,
                            SunspotNum int4 not null,
                            SunspotArea int4 not null,
                            NewRegions int4 not null,
                            XRayBkgdFlux float8 not null,                            
                            FlaresXRayC int4 not null,
                            FlaresXRayM int4 not null,
                            FlaresXRayX int4 not null,
                            FlaresOpticalS int4 not null,
                            FlaresOptical1 int4 not null,
                            FlaresOptical2 int4 not null,
                            FlaresOptical3 int4 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_swpc_flare_table finished!')


    ##创建kp表
    def create_element_kp_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_kp(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            kp int4 not null,
                            level varchar(10) not null,
                            descrip varchar(10) not null,                            
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_kp_table finished!')

        
    ##创建ap表
    def create_element_ap_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ap(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            ap int4 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ap_table finished!')

 
    ##创建dst表
    def create_element_dst_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_dst(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            dst int4 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_dst_table finished!')




    ##创建tec表
    def create_element_tec_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # site  写默认值北京站
        # TEC   写默认值-9999.0
        try:
            sqlcmd = '''create table element_tec(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            site varchar(10) not null,
                            tec float8 not null,
                            foF2 float8 not null,
                            foF1 float8 not null,
                            M float8 not null,
                            MUF float8 not null,
                            fmin float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_tec_table finished!')



    ##创建hpi表
    def create_element_hpi_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_hpi(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            NorthHPI float8 not null,
                            SouthHPI float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_hpi_table finished!')

        
        
    ##创建ste_swmag表
    def create_element_ste_sw_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ste_sw(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            Density float8 not null,
                            Speed float8 not null,
                            Temp float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ste_sw_table finished!')        
        
        
    ##创建ste_swmag表
    def create_element_ste_mag_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ste_mag(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            BR float8 not null,
                            BT float8 not null,
                            BN float8 not null,
                            Btotal float8 not null,
                            Lat float8 not null,
                            Lon float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ste_mag_table finished!')      

        
    ##创建ste_part表
    def create_element_ste_het_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ste_het(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            ProFlux_13to21Mev float8 not null,
                            ProFlux_40to100Mev float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ste_het_table finished!')           
        

    ##创建ace_swmag表
    def create_element_ace_sw_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ace_sw(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            Density float8 not null,
                            Speed float8 not null,
                            Temp float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ace_sw_table finished!')   


    ##创建ace_swmag表
    def create_element_ace_mag_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ace_mag(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            S int4 not null,
                            Bx float8 not null,
                            By float8 not null,
                            Bz float8 not null,
                            Bt float8 not null,
                            Lat float8 not null,
                            Lon float8 not null,
                            Bx_GSE float8 not null,
                            By_GSE float8 not null,
                            Bz_GSE float8 not null,                            
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ace_swmag_table finished!')   
        
        
    ##创建ace_part表
    def create_element_ace_ep_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ace_ep(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            EleS int4 not null,
                            EleDiffFlux_38to53 float8 not null,
                            EleDiffFlux_175to315 float8 not null,
                            ProS int4 not null,
                            ProDiffFlux_47to68 float8 not null,
                            ProDiffFlux_115to195 float8 not null,
                            ProDiffFlux_310to580 float8 not null,
                            ProDiffFlux_795to1193 float8 not null,
                            ProDiffFlux_1060to1900 float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ace_ep_table finished!')  



    ##创建ace_part表
    def create_element_ace_sis_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_ace_sis(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            ProFlux_GT10MeV float8 not null,
                            ProFlux_GT30MeV float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_ace_sis_table finished!') 
        
        
    ##创建goes_xr表
    def create_element_goes_xr_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_goes_xr(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            time_resolution varchar(4) not null,
                            XR_short float8 not null,
                            XR_long float8 not null,
                            level varchar(10) not null,
                            descrip varchar(10) not null,
                            HAF float8 not null,                            
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_goes_xr_table finished!')          
        
        
    ##创建goes_mag表
    def create_element_goes_mag_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_goes_mag(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            Hp float8 not null,
                            He float8 not null,
                            Hn float8 not null,                            
                            TotalField float8 not null,
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_goes_mag_table finished!')              
        
        
        
    ##创建goes_part表
    def create_element_goes_ie_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_goes_ie(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,                         
                            EFgt0d8M float8 not null,
                            EFgt2d0M float8 not null,                            
                            EFgt4d0M float8 not null,
                            IEFday float8 not null,
                            level varchar(10) not null,
                            descrip varchar(10) not null,                                                        
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_goes_ie_table finished!')    


    ##创建goes_part表
    def create_element_goes_ip_table(self, database_name):
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        try:
            sqlcmd = '''create table element_goes_ip(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            utc_time TIMESTAMP(0) not null,
                            satellite varchar(10) not null,
                            PFgt01M float8 not null,
                            PFgt05M float8 not null,
                            PFgt10M float8 not null,
                            PFgt30M float8 not null,
                            PFgt50M float8 not null,
                            PFgt100M float8 not null,
                            Ad float8 not null,
                            An float8 not null,
                            level varchar(10) not null,
                            descrip varchar(10) not null,                             
                            website varchar(30) not null,
                            category_abbr_en varchar(30) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        f_print('create_element_goes_ip_table finished!')    
        
        
    # ##创建t_task表
    # def create_t_task_table(self, database_name):
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # # serial自动增加
        # # 需要根据常用的变量创建索引，便于查询
        # # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # # 表字段不区分大小写
        
        # try:
            # sqlcmd = '''create table t_task(
                            # id serial not null primary key,
                            # task_name varchar(100) not null,
                            # task_triggers varchar(20) not null,
                            # task_hour varchar(128) not null,
                            # task_minute varchar(128) not null,
                            # task_second varchar(128) not null,
                            # data_class varchar(64) not null,
                            # research_area varchar(64) not null,
                            # website varchar(20) not null,
                            # category_abbr_en varchar(64) not null
                            # )'''
            # cursor.execute(sqlcmd)
        # except Exception as e:
            # print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # print('create_t_task_table finished!')
        
        
        
        
    ##创建task_monitor表
    #def create_t_task_monitor_table(self, database_name):    
    def create_data_monitor_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table data_monitor(
                            id serial not null primary key,
                            task_name varchar(100) not null,
                            create_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            log varchar(4096) not null,
                            status BOOLEAN not null,
                            cmd varchar(255) not null,
                            data_class varchar(64) not null,
                            research_area varchar(64) not null,
                            website varchar(20) not null,
                            category_abbr_en varchar(64) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_data_monitor_table finished!')


    ##创建task_monitor表
    #def create_t_task_monitor_table(self, database_name):    
    def create_product_monitor_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table product_monitor(
                            id serial not null primary key,
                            task_name varchar(100) not null,
                            create_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            log varchar(4096) not null,
                            status BOOLEAN not null,
                            data_class varchar(64) not null,
                            research_area varchar(64) not null,
                            website varchar(20) not null,
                            category_abbr_en varchar(64) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_product_monitor_table finished!')
        

    ##创建task_monitor表
    #def create_t_task_monitor_table(self, database_name):    
    def create_alert_monitor_table(self, database_name):
        """
        category_abbr_en名称不是数据收集里的英文标识种类，而是事件的区分标识
        
        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table alert_monitor(
                            id serial not null primary key,
                            task_name varchar(100) not null,
                            create_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            log varchar(4096) not null,
                            status BOOLEAN not null,
                            alert_type varchar(64) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_alert_monitor_table finished!')


        
    ##创建task_monitor表
    #def create_t_task_monitor_table(self, database_name):    
    def create_alert_file_info_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table alert_file_info(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            event_type varchar(20) not null,
                            bj_time TIMESTAMP(0) not null,
                            event_level varchar(10) not null, 
                            event_descrip varchar(10) not null,     
                            sms varchar(255) not null,                            
                            log varchar(4096) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_alert_file_info_table finished!')


        
    ##创建task_monitor表
    #def create_t_task_monitor_table(self, database_name):    
    def create_product_file_info_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table product_file_info(
                            id serial not null primary key,
                            category_abbr_en varchar(255) not null,
                            filename varchar(255) not null,
                            path varchar(255) not null,
                            record_time TIMESTAMP(0) not null,
                            start_time TIMESTAMP(0) not null,
                            end_time TIMESTAMP(0) not null,
                            file_size integer not null,
                            log varchar(4096) not null                            
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_product_file_info_table finished!')



    # def create_contact_group_table(self, database_name):
        # """

        # """
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # # serial自动增加
        # # 需要根据常用的变量创建索引，便于查询
        # # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # # 表字段不区分大小写
        # # 实际测试发现log日志有超过255的长度,最长设置到1024
        # try:
            # #sqlcmd = '''create table t_task_monitor(        
            # sqlcmd = '''create table contact_group(
                            # id serial not null primary key,
                            # group_name varchar(10) not null,
                            # create_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,                            
                            # state BOOLEAN not null                            
                            # )'''
            # cursor.execute(sqlcmd)
        # except Exception as e:
            # f_print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # #print('create_t_task_monitor_table finished!')
        # f_print('create_contact_group_table finished!')
        
      

    def create_contact_group_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table contact_group(
                            id varchar(50) not null primary key,
                            group_name varchar(10) not null,
                            create_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,                            
                            state BOOLEAN not null                            
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_contact_group_table finished!')

        
    # def create_contact_info_table(self, database_name):
        # """

        # """
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # # serial自动增加
        # # 需要根据常用的变量创建索引，便于查询
        # # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # # 表字段不区分大小写
        # # 实际测试发现log日志有超过255的长度,最长设置到1024
        # try:
            # #sqlcmd = '''create table t_task_monitor(        
            # sqlcmd = '''create table contact_info(
                            # id serial not null primary key,
                            # group_id integer not null,
                            # name varchar(10) not null,
                            # phone varchar(15) not null,                            
                            # create_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null
                            # )'''
            # cursor.execute(sqlcmd)
        # except Exception as e:
            # f_print(e)
            # # exit()
        # conn.commit()
        # conn.close()
        # #print('create_t_task_monitor_table finished!')
        # f_print('create_contact_info_table finished!')


    def create_contact_info_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table contact_info(
                            id serial not null primary key,
                            group_id varchar(50) not null,
                            name varchar(10) not null,
                            phone varchar(15) not null,                            
                            create_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_contact_info_table finished!')
        
        
    def create_event_configuration_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table event_configuration(
                            id serial not null primary key,
                            category varchar(20) not null,
                            level varchar(5) not null,
                            descrip varchar(5) not null,
                            measure float8 not null,                            
                            level_number varchar(2) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_event_configuration_table finished!')
        
        
        
    def create_report_file_info_table(self, database_name):
        """
        1. 创建报告记录
        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        # serial自动增加
        # 需要根据常用的变量创建索引，便于查询
        # 查询时候，也使用复合索引查询，另外插入的时效性要求不高，可以建立复合索引，查询效率高
        # 表字段不区分大小写
        # 实际测试发现log日志有超过255的长度,最长设置到1024
        try:
            #sqlcmd = '''create table t_task_monitor(        
            sqlcmd = '''create table report_file_info(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            event_type varchar(20) not null,
                            utc_date_begin TIMESTAMP(0) not null,
                            utc_date_end TIMESTAMP(0) not null,
                            event_level varchar(10) not null,
                            event_Pmax float8 not null,
                            path varchar(255) not null,
                            filename varchar(255) not null,                            
                            log varchar(4096) not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
            # exit()
        conn.commit()
        conn.close()
        #print('create_t_task_monitor_table finished!')
        f_print('create_report_file_info_table finished!')
        
        
    # def create_clean_up_monitor_table(self, database_name):
        # """
        # 1. 创建删除状态记录,前端界面查询此表作为删除状态的依据
        # 2. 前端界面,每次打开,去查询此数据库状态,先入库1条初始化记录,状态为false,入库完成更改为true
        # """
        # conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                # port=self.port)
        # cursor = conn.cursor()
        # try:     
            # sqlcmd = '''create table clean_up_monitor(
                            # id serial not null primary key,
                            # table_name varchar(40) not null,
                            # record_time TIMESTAMP(0) not null,
                            # update_time TIMESTAMP(0) not null,
                            # start_time TIMESTAMP(0) not null,
                            # end_time TIMESTAMP(0) not null,
                            # status BOOLEAN not null
                            # )'''
            # cursor.execute(sqlcmd)
        # except Exception as e:
            # f_print(e)
        # conn.commit()
        # conn.close()
        # f_print('create_clean_up_monitor_table finished!')        
        

    def create_clean_up_monitor_table(self, database_name):
        """
        1. 创建删除状态记录,前端界面查询此表作为删除状态的依据
        2. 前端界面,每次打开,去查询此数据库状态,先入库1条初始化记录,状态为false,入库完成更改为true
        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        try:     
            sqlcmd = '''create table clean_up_monitor(
                            id serial not null primary key,
                            table_name varchar(40) not null,
                            record_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            start_time TIMESTAMP(0) not null,
                            end_time TIMESTAMP(0) not null,
                            status int2 not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
        conn.commit()
        conn.close()
        f_print('create_clean_up_monitor_table finished!')        

        
    def create_export_monitor_table(self, database_name):
        """
        1. 创建删除状态记录,前端界面查询此表作为删除状态的依据
        2. 前端界面,每次打开,去查询此数据库状态,先入库1条初始化记录,状态为false,入库完成更改为true
        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        try:     
            sqlcmd = '''create table export_monitor(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            start_time TIMESTAMP(0) not null,
                            end_time TIMESTAMP(0) not null,
                            filesize float8 not null,
                            status BOOLEAN not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
        conn.commit()
        conn.close()
        f_print('create_export_monitor_table finished!')   


    def create_import_monitor_table(self, database_name):
        """
        1. 创建删除状态记录,前端界面查询此表作为删除状态的依据
        2. 前端界面,每次打开,去查询此数据库状态,先入库1条初始化记录,状态为false,入库完成更改为true
        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        try:     
            sqlcmd = '''create table import_monitor(
                            id serial not null primary key,
                            record_time TIMESTAMP(0) not null,
                            update_time TIMESTAMP(0) not null,
                            start_time TIMESTAMP(0) not null,
                            end_time TIMESTAMP(0) not null,
                            filesize float8 not null,
                            status int2 not null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
        conn.commit()
        conn.close()
        f_print('create_import_monitor_table finished!')
        
        
    def create_element_info_table(self, database_name):
        """

        """
        conn = psycopg2.connect(database=database_name, host=self.host, user=self.user, password=self.password,
                                port=self.port)
        cursor = conn.cursor()
        try:     
            sqlcmd = '''create table element_info(
                            id serial not null primary key,
                            element_name_zh varchar(255) not null,
                            element_name_en varchar(50) null,
                            website varchar(255) not null,
                            total_arrive int4 not null,
                            table_name varchar(50) not null,
                            gain_amount int4 null,
                            arrival_rate varchar(10) null,
                            update_time TIMESTAMP(0) null
                            )'''
            cursor.execute(sqlcmd)
        except Exception as e:
            f_print(e)
        conn.commit()
        conn.close()
        f_print('create_element_info_table finished!')
        

        