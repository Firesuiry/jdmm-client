import socket
import struct

from common import *

BUFFER_SIZE = 1024

class Sender:
    def __init__(self):
        port = 51303
        self.host = get_Local_ipv6_address()
        print('当前host：{}'.format(self.host))
        if not self.host:
            print('no host')
            exit()

        self.client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.client.bind((self.host, port))

    def __del__(self):
        print('执行析构函数')
        self.client.close()


    def send_file(self,sock:socket.socket=None):
        if not sock:
            sock = self.client
        file_path = r'D:\webDevelop\client\new.png'
        file_path = r'new.png'
        file_name, file_name_len, file_size, md5 = get_file_info(file_path)
        file_head = struct.pack(HEAD_STRUCT, bytes(file_name,encoding='utf-8'), file_name_len,
                                file_size, bytes(md5,encoding='utf-8'))
        print('文件大小:{}'.format(file_size))
        server_address = (self.host, 113)
        print("Start connect")
        sock.connect(server_address)
        sock.send(file_head)
        sent_size = 0

        with open(file_path,'rb') as fr:
            while sent_size < file_size:
                remained_size = file_size - sent_size
                print('剩余字节：{}'.format(remained_size))
                send_size = BUFFER_SIZE if remained_size > BUFFER_SIZE else remained_size
                send_file = fr.read(send_size)
                sent_size += send_size
                sock.send(send_file)

if __name__ == '__main__':
    sender = Sender()

    sender.send_file()
