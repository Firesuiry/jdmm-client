from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import hashlib
from common import *

def generate_pwd(fileID,secret):
    str_in = '{}{}'.format(fileID,secret)
    m = hashlib.md5(str_in.encode('utf-8'))
    return m.hexdigest()


class FtpServer:

    def __init__(self):
        pass

    def start_easy_share_server(self, ip, path):
        authorizer = DummyAuthorizer()
        authorizer.add_anonymous(path)
        handler = FTPHandler
        handler.authorizer = authorizer
        server = FTPServer((ip, 21), handler)
        server.serve_forever()

    def start_jdmm_file_server(self, ip, fileIDs, secret, base_dir, port=21):
        authorizer = DummyAuthorizer()
        # authorizer.add_anonymous('{}/index/'.format(base_dir))

        print('启动FTP服务器 文件ID：{}'.format(fileIDs))
        for fileID in fileIDs:
            usr = fileID
            pwd = generate_pwd(fileID,secret)
            path = '{}/{}/'.format(base_dir,fileID)
            print('设置分享信息 用户名：{} 密码：{} 路径：{}'.format(usr,pwd,path))
            authorizer.add_user(str(usr), pwd, path, perm='elr')

        handler = FTPHandler
        handler.authorizer = authorizer
        server = FTPServer((ip, 21), handler)
        server.serve_forever()

if __name__ == '__main__':
    ipv6 = get_Local_ipv6_address()
    fileIDs = [1,2]
    secret = 'test'
    base_dir = r'D:\webDevelop\test_base'
    ftp =FtpServer()
    ftp.start_jdmm_file_server(ipv6,fileIDs,secret,base_dir)
