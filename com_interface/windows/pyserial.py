# -*- coding: utf-8 -*-




"""
@user guide
1. 每条命令之间时间间隔必须大于 300ms 发送
2. 校验位: N－无校验，E－偶校验，O－奇校验
3. 生成一个 CRC 的流程为：
（1） 预置一个 16 位寄存器为 OFFFFH（16 进制， 全 1） ,称之为 CRC 寄存器。
（2） 把数据帧中的第一个字节的 8 位与 CRC 寄存器中的低字节进行异或运算， 结果存回 CRC寄存器。
（3） 将 CRC 寄存器向右移一位， 最高位填以 0， 最低位移出并检测。
（4） 上一步中被移出的那一位如果为 0： 重复第三步（下一次移位） ； 为 1： 将 CRC 寄存器与一个预设的固定值（多项式 A001H） 进行异或运算。
（5） 重复第三点和第四步直到 8 次移位。 这样处理完了一个完整的八位。
（6） 重复第 2 步到第 5 步来处理下一个八位， 直到所有的字节处理结束。
（7） 最终 CRC 寄存器的值就是 CRC 的值。
4. 
地址码         功能码         数据码               校验码
1 个 BYTE      1 个 BYTE      N 个 BYTE            2 个 BYTE

5.
地址    命令    起始寄存器地址（高位）    起始寄存器地址（低位）    寄存器个数（高位）    寄存器个数（低位）    CRC16 低位    CRC16 高位



@modify history

                    
"""

import os
import sys
import time
import datetime
import traceback
import binascii
import serial  # 导入模块
import serial.tools.list_ports


class Pyserial:
    def __init__(self):
        self.ser = serial.Serial(port='COM3', baudrate = 9600, bytesize = 8,parity = 'N',stopbits = 1,timeout=1)

    def get_com_port(self):
        port_list = list(serial.tools.list_ports.comports())
        print(port_list)
        if len(port_list) == 0:
            print('无可用串口')
        else:
            for i in range(0, len(port_list)):
                print('可用端口: ',port_list[i])
    
    def crc16(self, x, invert):
        a = 0xFFFF
        b = 0xA001
        for byte in x:
            #print ('byte = ',byte)
            #a ^= ord(str(byte))
            a ^= byte           
            for i in range(8):
                last = a % 2
                a >>= 1
                if last == 1:
                    a ^= b
        s = hex(a).upper()
        
        return s[4:6]+s[2:4] if invert == True else s[2:4]+s[4:6]


    def string2hex(self,string_cmd):
        strHex = binascii.b2a_hex(string_cmd)  
        hex_cmd = strHex.decode("hex")  
        return hex_cmd


    def send_cmd(self, cmd):
        try:
            # 端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
            #portx = "COM3"
            # 波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
            #bps = 9600
            # 超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）
            #timex = 1
            # 打开串口，并得到串口对象
            #ser = serial.Serial(port='COM3', baudrate = 9600, bytesize = 8,parity = 'N',stopbits = 1,timeout=1)

            # 写数据
            # result=ser.write("我是东小东".encode("gbk"))
            #result = self.ser.write(cmd.encode("utf-8"))
            print ('发送指令: ',cmd)
            time.sleep(0.5)##sleep单位是秒,300ms以上
            result = self.ser.write(cmd)
            #result = self.ser.write(cmd.encode("gbk"))
            #result = self.ser.write(cmd.encode())            
            print("写总字节数:", result)

        except Exception as e:
            print("---异常---：", e)

    def close_port(self):
        print ('关闭串口.')
        self.ser.close()  # 关闭串口
        return 
        
        
    def receive_cmd(self, cmd):
        try:
            # 端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
            # portx = "COM3"
            # # 波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
            # bps = 9600
            # # 超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）
            # timex = 5
            # # 打开串口，并得到串口对象
            # #ser = serial.Serial(portx, bps, timeout=timex)

            # 写数据
            # result=ser.write("我是东小东".encode("gbk"))
            result = self.ser.read()
            print("读总字节数:", result)

            self.ser.close()  # 关闭串口

        except Exception as e:
            print("---异常---：", e)


if __name__ == "__main__":
    ps = Pyserial()
    
    
    ##计算crc
    crc = ps.crc16( x=[0x01,0x06,0x00,0x10,0x00,0x02], invert = 'False')
    print ('打开警报灯 crc = ',crc)
    crc = ps.crc16( x=[0x01,0x06,0x00,0x10,0x00,0x03], invert = 'False')
    print ('打开警报 crc = ',crc)
    crc = ps.crc16( x=[0x01,0x06,0x00,0x11,0x00,0x00], invert = 'False')
    print ('调整音量0级 crc = ',crc)
    crc = ps.crc16( x=[0x01,0x06,0x00,0x12,0x01,0x02], invert = 'False')
    print ('调整音调,第一个文件夹第二个曲目 crc = ',crc)       
    crc = ps.crc16( x=[0x01,0x06,0x00,0x10,0x00,0x00], invert = 'False')
    print ('关闭警报 crc = ',crc)    
    #input()

    ps.get_com_port()                               # 获取系统中端口

    ##测试1
    # cmd2 = '01 06 00 10 00 02 09 CE'              # 打开警报灯    
    # cmd3 = '01 06 00 10 00 00 88 0F'              # 关闭警报 

    ##测试2
    #cmd2 = "01060010000209CE\r\n"                  # 打开警报灯
    
    ##测试3    
    # cmd2 = "01060010000209CE"                     # 打开警报灯      
    # cmd3 = "010600100000880F"                     # 关闭警报  

    ##测试4
    cmd1 = [0x01,0x06,0x00,0x10,0x00,0x02,0x09,0xCE]                # 打开警报灯      
    cmd2 = [0x01,0x06,0x00,0x10,0x00,0x03,0xC8,0x0E]                # 打开警报
    cmd3 = [0x01,0x06,0x00,0x11,0x00,0x00,0xD9,0xCF]                # 调整音量0级
    cmd4 = [0x01,0x06,0x00,0x12,0x01,0x02,0xA9,0x9E]                # 调整音调,第一个文件夹第二个曲目   
    cmd5 = [0x01,0x06,0x00,0x10,0x00,0x00,0x88,0x0F]                # 关闭警报  


    #cmd22 = ps.string2hex(cmd2)
    #cmd33 = ps.string2hex(cmd3)
    # print (cmd2)    
    # print (cmd3)    
    
    ##发送命令
    ps.send_cmd(cmd1)
    ps.send_cmd(cmd2)
    ps.send_cmd(cmd3)
    ps.send_cmd(cmd4)
    ps.send_cmd(cmd5)
    
    ##关闭串口
    ps.close_port()
    
    