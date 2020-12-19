import ctypes
import time
import zipfile

import requests
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog
from data import *

from common import *
import pathlib

from ftp_server import FtpServer


def create_zip_file(files, target):
    f = zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED)
    for file in files:
        print('添加{}到压缩文件{}'.format(file, target))
        f.write(file, file.split('/')[-1])
    f.close()


class PublistWorker(QThread):
    pub_finish_signal = Signal(str, int)

    def __init__(self, cookie, title, des, money, cate, tiquma, unpress_pwd, file_format, file_size):
        super(PublistWorker, self).__init__()
        self.cookie = cookie

        self.title = title
        self.des = des
        self.money = money
        self.cate = cate
        self.tiquma = tiquma
        self.unpress_pwd = unpress_pwd
        self.file_format = file_format
        self.file_size = file_size

    def run(self):
        try:
            id, msg = self.upload_file_infor()
            self.pub_finish_signal.emit(str(msg), id)
        except Exception as e:
            self.pub_finish_signal.emit(str(e), -1)

    def upload_file_infor(self):
        """
        :param title:
        :param des:
        :param money:
        :param cate:
        :param tiquma:
        :param unpress_pwd:
        :param file_format:
        :param file_size:
        :return: 文件ID
        """
        title = self.title
        des = self.des
        money = self.money
        cate = self.cate
        tiquma = self.tiquma
        unpress_pwd = self.unpress_pwd
        file_format = self.file_format
        file_size = self.file_size

        if not title:
            raise ValueError('没有定义标题')

        if not des:
            des = title

        if not money:
            raise ValueError('没有提供有效价格')

        data = {
            'title': title,
            'money': int(float(money) * 100),
            'markdown_describe': des,
            'download_url': 'CLIENT',
            'tiquma': tiquma,
            'unzip_password': unpress_pwd,
            'file_format': file_format,
            'file_size': file_size,
            'category': cate
        }
        print(data)
        res = requests.post(FILE_UPLOAD_URL, data, cookies=self.cookie)
        data = res.json()
        code = data.get('code')
        if code < 300:
            id = data['detail']['id']
            return id, data.get('msg')
        else:
            raise ValueError('发布失败 原因：{}'.format(data.get('msg')))


def update_ftp_auth_info():
    """

    :return:
    """


class HttpWorker(QThread):
    finish_signal = Signal(requests.Response)

    def __init__(self, url, method='GET', data=None, cookie=None):
        super(HttpWorker, self).__init__()
        self.url = url
        self.method = method
        self.data = data
        self.cookie = cookie

    def run(self):
        if self.method == 'GET':
            res = requests.get(url=self.url, data=self.data, cookies=self.cookie)
        else:
            res = requests.post(url=self.url, data=self.data, cookies=self.cookie)
        self.finish_signal.emit(res)


class UpdateInfoWorker(QThread):
    info_change_signal = Signal(str)

    def __init__(self, clientid, ipv6host, port, secret, mac, cookie):
        super(UpdateInfoWorker, self).__init__()
        self.clientid = clientid
        self.ip = ipv6host
        self.port = port
        self.secret = secret
        self.mac = mac
        self.cookie = cookie
        self.init = False

        self.remain_time = 0

    def run(self):
        while True:
            if self.remain_time <= 0:
                self.send_alive_signal()
                self.remain_time = 30
                continue
            self.remain_time -= 1
            self.info_change_signal.emit('等待下次上报服务器信息 剩余时间:{}'.format(self.remain_time))
            time.sleep(1)

    def update_info_on_server(self, ipv6host, port, fileIDs, secret):
        """
        更新在服务器上的文件分享信息
        :param ipv6host:
        :param port:
        :param fileIDs:
        :return:
        """

    def send_alive_signal(self):
        data = {
            'ipv6':self.ip,
            'mac': self.mac,
            'secret':self.secret,
            'pk':self.clientid
        }
        res = requests.post(CLIENT_INFO_URL,data,cookies=self.cookie)
        self.info_change_signal.emit('L更新信息完成 响应:{}'.format(res.json()))




class initWorker(QThread):
    init_finish_signal = Signal(dict)

    def __init__(self, mac, main):
        super(initWorker, self).__init__()
        self.mac = mac
        self.main = main

    def run(self):
        print(self.main.cookie)
        res = requests.get(CLIENT_INFO_URL + '?mac={}'.format(self.mac), cookies=self.main.cookie)
        print(res.json())
        self.init_finish_signal.emit(res.json())


class JdmmFileFtpServerWorker(QThread):
    def __init__(self, ip, fileIDs, secret, base_dir):
        super(JdmmFileFtpServerWorker, self).__init__()
        self.ip = ip
        self.fileIDs = fileIDs
        self.secret = secret
        self.base_dir = base_dir
        self.ftp_server = None

    def run(self):
        self.ftp_server = FtpServer()
        self.ftp_server.start_jdmm_file_server(self.ip, self.fileIDs, self.secret, self.base_dir)


class JdmmFileServer:
    def __init__(self, window, main):
        self.window = window
        self.main = main
        self.add_log('正在初始化文件服务器')
        self.mac = get_MAC()
        self.ipv6 = get_Local_ipv6_address()
        self.file_names = []
        self.basedir = get_key('client_base_dir')
        self.secret = get_MAC()
        self.clientID = -1
        self.file_nums = -1
        self.share_file_names = []
        self.remote_share_file_names = []
        self.ftp_server = None
        self.info_update_worker = None

        self.file_name_buffer = []

        self.window.client_mac_label.setText(self.mac)
        self.window.client_ipv6_label.setText(self.ipv6)
        self.window.client_base_path_label.setText(self.basedir)
        self.window.client_secret_label.setText(self.mac)

        self.window.client_choose_files_btn.clicked.connect(self.on_set_files_btn_clicked)
        self.window.client_upload_btn.clicked.connect(self.on_upload_btn_clicked)
        self.window.client_set_base_path_btn.clicked.connect(self.on_set_base_path_btn_clicked)
        self.window.client_clear_log_btn.clicked.connect(self.on_clear_log_btn_clicked)
        self.window.client_restart_btn.clicked.connect(self.on_restart_btn_clicked)
        self.window.client_registe_client_btn.clicked.connect(self.on_registe_client_btn)

        self.init_worker = initWorker(self.mac, self.main)
        self.init_worker.init_finish_signal.connect(self.on_init_finished)
        self.add_log('基本信息初始化完成 登录后继续初始化')


    def reconfig(self):
        self.mac = get_MAC()
        self.ipv6 = get_Local_ipv6_address()
        self.secret = get_MAC()


    def on_login_success(self):
        self.add_log('检测客户端状态')
        self.init_worker.start()

    def get_cookie(self):
        return self.main.cookie

    def on_init_finished(self, data):
        code = data.get('code')
        if code == 400:
            self.add_log('当前客户端未注册')
            self.window.client_id_label.setText('当前客户端未注册')
            self.window.client_connect_state_label.setText('已获得服务器响应')
            self.add_log('如需将本机设置为文件分享服务器 请点击注册客户端')
            self.add_log('分享需要确保 1.本机21端口畅通 2.本机支持ipv6')
            self.add_log('如未登录请先登录')
        elif code == 200:
            self.clientID = int(data['data']['id'])
            self.remote_share_file_names = data['data']['files']

            self.add_log('当前客户端已注册 ID：{}'.format(self.clientID))
            self.window.client_id_label.setText('当前客户端已注册 ID：{}'.format(self.clientID))
            self.window.client_connect_state_label.setText('已获得服务器响应')

            self.update_share_files()
        self.add_log('初始化全部完成')

    def update_share_files(self):
        base = pathlib.Path(self.basedir)
        files = base.glob('*')
        self.share_file_names.clear()
        for file in files:
            if file.name.isdigit() and int(file.name) > 2000000:
                if os.path.exists(file.joinpath('file.zip')):
                    self.share_file_names.append(file.name)
        self.restart_share_server()

        self.file_name_buffer.clear()
        for name in self.share_file_names:
            if not int(name) in self.remote_share_file_names:
                # 添加id到服务器
                print(name, self.remote_share_file_names)
                self.file_name_buffer.append(name)
        self.on_update_share_files_finished_one()

    def on_update_share_files_finished_one(self):
        if len(self.file_name_buffer) < 1:
            self.add_log('更新分享文件结束')
            return
        fileid = self.file_name_buffer.pop(0)
        print('添加ID：{} 到服务器'.format(fileid))
        data = {
            'action': 'add',
            'ipv6': self.ipv6,
            'mac': self.mac,
            'pk': self.clientID,
            'file': fileid
        }
        self.update_share_file_http = HttpWorker(CLIENT_INFO_URL, 'POST', data, self.main.cookie)
        self.update_share_file_http.finish_signal.connect(self.on_update_share_files_finished_one)
        self.update_share_file_http.start()

    def restart_share_server(self):
        self.add_log('正在尝试重启文件分享服务器')
        self.reconfig()
        if self.ftp_server:
            try:
                print(' 关闭FTP服务器')
                self.ftp_server.stop()
                self.ftp_server.wait()
                print(' 关闭FTP服务器完成')
            except Exception as e:
                print(e)
        print('分享文件列表：{}'.format(self.share_file_names))
        self.window.client_file_num_label.setText(str(len(self.share_file_names)))
        self.ftp_server = JdmmFileFtpServerWorker(self.ipv6, self.share_file_names, self.mac, self.basedir)
        self.ftp_server.start()

        if self.info_update_worker:
            try:
                self.info_update_worker.stop()
                self.info_update_worker.wait()
            except Exception as e:
                print(e)
        self.info_update_worker = UpdateInfoWorker(self.clientID,self.ipv6,21,self.secret,self.mac,self.main.cookie)
        self.info_update_worker.info_change_signal.connect(self.on_info_update_msg)
        self.info_update_worker.start()

    def on_info_update_msg(self,msg):
        if msg[0] == 'L':
            self.add_log(msg[1:])
        else:
            self.window.client_connect_state_label.setText(msg)

    def on_set_files_btn_clicked(self):
        file_names = QFileDialog.getOpenFileNames(self.window, "选择分享的文件", r"C:\Users\Administrator\Desktop")
        self.file_names = file_names[0]
        self.add_log('当前选择的文件：')
        for file_name in self.file_names:
            self.add_log(file_name)

    def on_set_base_path_btn_clicked(self):
        path = QFileDialog.getExistingDirectory(self.window, "选择文件夹", "/")
        if path == '':
            self.add_log('工作目录为空 设置失败')
            return
        self.add_log('设置工作文件目录：{}'.format(path))
        self.basedir = path
        self.window.client_base_path_label.setText(path)
        set_key('client_base_dir', self.basedir)
        self.on_restart_btn_clicked()

    def on_clear_log_btn_clicked(self):
        self.window.client_log_text.clear()

    def on_restart_btn_clicked(self):
        self.add_log('当前重启有问题  请关闭客户端后再打开以重启')
        return
        self.restart_share_server()

    def on_registe_client_btn(self):
        self.add_log('尝试注册客户端到服务器')
        if not self.main.check_login():
            self.add_log('未登录 请先登录后再操作')
            return
        data = {
            'ipv6': self.ipv6,
            'port': 21,
            'secret': self.mac,
            'mac': self.mac
        }
        self.registe_client_http = HttpWorker(CLIENT_INFO_URL, method='POST', data=data, cookie=self.main.cookie)
        self.registe_client_http.finish_signal.connect(self.on_registe_finished)
        self.registe_client_http.start()

    def on_registe_finished(self, res):
        self.add_log('获得服务器返回信息')
        print(res.json())

    def on_upload_btn_clicked(self):
        print('点击上传按钮')
        if not self.main.check_login():
            self.add_log('未登录 请先登录后再上传')
            return

        title = self.window.client_title_input.text()
        des = self.window.client_des_input.toPlainText()
        unpress_pwd = self.window.client_unpress_pwd_input.text()
        money = self.window.client_money_input.text()
        file_format = 'ZIP'
        file_size = 0
        for file_name in self.file_names:
            file_size += os.path.getsize(file_name)
        if file_size < 1:
            self.add_log('请重新选择要上传的文件 当前可能选择失败')
            return
        file_size = '{}'.format(round(file_size / 1024 / 1024, 5))[:7] + 'MB'
        cate = int(self.window.client_cate_cb.currentText().split('|')[0])

        self.upload_worker = PublistWorker(self.main.cookie, title, des, money, cate, '', unpress_pwd, file_format,
                                           file_size)
        self.upload_worker.pub_finish_signal.connect(self.on_upload_finished)
        self.upload_worker.start()

    def on_upload_finished(self, msg, id):
        if id < 0:
            self.add_log('上传失败 原因：{}'.format(msg))
            return
        self.add_log('上传成功：{}'.format(msg))
        new_path = '{}/{}/'.format(self.basedir, id)
        zip_path = '{}{}'.format(new_path, 'file.zip')
        if not os.path.exists(new_path):
            os.mkdir(new_path)
        create_zip_file(self.file_names, zip_path)
        self.file_names.clear()
        self.on_restart_btn_clicked()

    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.client_log_text.append(str(msg))
        self.window.client_log_text.moveCursor(self.window.client_log_text.textCursor().End)


if __name__ == '__main__':
    files = ['client.ui', 'data.py']
    create_zip_file(files)
