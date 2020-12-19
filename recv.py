'''
github.com/razyar

if you want convert or send, send converted version change -> recv_file = open('AnyName.newformat or orginal format', 'wb')
'''
import hashlib
import os
import struct
import sys
import socket
from common import *


def unpack_file_info(file_info):
    file_name, file_name_len, file_size, md5 = struct.unpack(HEAD_STRUCT, file_info)
    file_name = file_name[:file_name_len]
    return file_name, file_size, md5


class Client:
    def __init__(self):
        port = 113
        self.host = get_Local_ipv6_address()
        print('当前host：{}'.format(self.host))
        if not self.host:
            print('no host')
            exit()

        self.client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.client.bind((self.host, port))
        self.client.listen(10)
        self.listen()

    def listen(self):
        recv_file = open('new2.png', 'wb')
        c, addr = self.client.accept()
        print('File will recv from: ', addr)
        print('Start recv...')

        info_size = struct.calcsize(HEAD_STRUCT)
        print('结构体大小:{}'.format(info_size))
        file_info_package = self.client.recv(info_size)
        file_name, file_size, md5_recv = unpack_file_info(file_info_package)
        print(file_name,file_size,md5_recv)
        while True:
            file2recv = c.recv(4096)
            print('recv 4096')
            while (file2recv):
                print("Receiving...")
                recv_file.write(file2recv)
                file2recv = c.recv(4096)
            print("File recv or converted successfully.")
            recv_file.close()
            c.close()

if __name__ == '__main__':
    client = Client()

