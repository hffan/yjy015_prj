2020-08-10 17:05:51
使用root用户
0. cd /home/YJY015/code/com_interface/linux/driver/libftd2xx-x86_64-1.3.6/release
1. cd build
2. cp libftd2xx.* /usr/local/lib
3. chmod 0755 /usr/local/lib/libftd2xx.so.1.3.6
4. ln -sf /usr/local/lib/libftd2xx.so.1.3.6 /usr/local/lib/libftd2xx.so


5. 查看系统中串口
(base) [root@localhost linux]# ls -l /dev/ttyS*
crw-rw----. 1 root dialout 4, 64 8月   3 10:19 /dev/ttyS0
crw-rw----. 1 root dialout 4, 65 8月   3 10:19 /dev/ttyS1
crw-rw----. 1 root dialout 4, 66 8月   3 10:19 /dev/ttyS2
crw-rw----. 1 root dialout 4, 67 8月   3 10:19 /dev/ttyS3



6.检查串口设备
(base) [root@localhost ~]#  dmesg | grep ttyS*
[628306.566356] usb 1-3: FTDI USB Serial Device converter now attached to ttyUSB0
[628347.675635] ftdi_sio ttyUSB0: FTDI USB Serial Device converter now disconnected from ttyUSB0
[628382.835679] usb 1-3: FTDI USB Serial Device converter now attached to ttyUSB0


7. python pyserial.py
可用端口:  /dev/ttyS0 - n/a
可用端口:  /dev/ttyUSB0 - FT232R USB UART

8.
(base) [root@localhost code]# python pyserial.py 
Linux
打开警报灯 crc =  CE09
打开警报 crc =  EC8
调整音量0级 crc =  CFD9
调整音量1级 crc =  F18
调整音调,第一个文件夹第二个曲目 crc =  9EA9
关闭警报 crc =  F88
[<serial.tools.list_ports_linux.SysFS object at 0x7f4bf6468c88>, <serial.tools.list_ports_linux.SysFS object at 0x7f4bf6444e80>]
可用端口:  /dev/ttyS0 - n/a
可用端口:  /dev/ttyUSB0 - FT232R USB UART
发送指令:  [1, 6, 0, 16, 0, 2, 9, 206]
写总字节数: 8
发送指令:  [1, 6, 0, 16, 0, 3, 200, 14]
写总字节数: 8
发送指令:  [1, 6, 0, 17, 0, 1, 24, 15]
写总字节数: 8
发送指令:  [1, 6, 0, 18, 1, 2, 169, 158]
写总字节数: 8
发送指令:  [1, 6, 0, 16, 0, 0, 136, 15]
写总字节数: 8
关闭串口.



