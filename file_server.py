import time
import requests
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog
from common import *


class PublistWorker(QThread):
    pub_finish_signal = Signal(str, int)

    def __init__(self, cookie, title, des, money, cate, tiquma, unpress_pwd, file_format, file_size, client_id,
                 file_name):
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
        self.client_id = client_id
        self.file_name = file_name

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
            'download_url': 'CLIENT|{}|{}'.format(self.client_id, self.file_name),
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
            'ipv6': self.ip,
            'mac': self.mac,
            'secret': self.secret,
            'pk': self.clientid
        }
        res = requests.post(CLIENT_INFO_URL, data, cookies=self.cookie)
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


class JdmmFileServer:
    def __init__(self, window, main):
        self.window = window
        self.main = main
        self.add_log('正在初始化文件服务器')
        self.mac = get_MAC()
        self.ipv6 = get_Local_ipv6_address()
        self.secret = get_MAC()
        self.clientID = -1
        self.file_nums = -1
        self.fid = ''
        self.file_name = ''
        self.file_data = {}

        self.current_choose_file = ''

        self.window.client_mac_label.setText(self.mac)
        self.window.client_ipv6_label.setText('')

        self.window.client_choose_files_btn.clicked.connect(self.on_set_files_btn_clicked)
        self.window.client_choose_files_btn_2.clicked.connect(self.on_set_files_btn_clicked)
        self.window.client_upload_btn.clicked.connect(self.on_upload_btn_clicked)
        self.window.client_clear_log_btn.clicked.connect(self.on_clear_log_btn_clicked)
        self.window.client_registe_client_btn.clicked.connect(self.on_registe_client_btn)
        self.window.check_file_btn.clicked.connect(self.on_check_file_btn_clicked)
        self.window.set_file_download_btn.clicked.connect(self.on_set_file_download_btn_clicked)

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
            self.add_log('如需将本机设置为文件分享服务器 请点击注册客户端')
            self.add_log('如未登录请先登录')
        elif code == 200:
            self.clientID = int(data['data']['id'])
            self.remote_share_file_names = data['data']['files']
            self.ipv6 = data['data']['ipv6']
            self.window.client_ipv6_label.setText(self.ipv6)

            self.add_log('当前客户端已注册 ID：{}'.format(self.clientID))
            self.window.client_id_label.setText('当前客户端已注册 ID：{}'.format(self.clientID))

        self.add_log('初始化全部完成')

    def on_info_update_msg(self, msg):
        if msg[0] == 'L':
            self.add_log(msg[1:])
        else:
            self.window.client_connect_state_label.setText(msg)

    def on_set_files_btn_clicked(self):
        file_names = QFileDialog.getOpenFileName(self.window, "选择分享的文件", r"C:\Users\Administrator\Desktop")
        self.file_name = file_names[0]
        self.add_log('当前选择的文件：')
        self.add_log(self.file_name)

    def on_clear_log_btn_clicked(self):
        self.window.client_log_text.clear()

    def on_registe_client_btn(self):
        self.add_log('尝试注册客户端到服务器')
        if not self.main.check_login():
            self.add_log('未登录 请先登录后再操作')
            return
        data = {
            'ipv6': self.ipv6,
            'port': 8080,
            'secret': self.mac,
            'mac': self.mac
        }
        self.registe_client_http = HttpWorker(CLIENT_INFO_URL, method='POST', data=data, cookie=self.main.cookie)
        self.registe_client_http.finish_signal.connect(self.on_registe_finished)
        self.registe_client_http.start()

    def on_registe_finished(self, res):
        self.add_log('获得服务器返回信息')
        print(res.json())
        self.init_worker = initWorker(self.mac, self.main)
        self.init_worker.init_finish_signal.connect(self.on_init_finished)
        self.init_worker.start()

    def on_upload_btn_clicked(self):
        print('点击上传按钮')
        if not self.main.check_login():
            self.add_log('未登录 请先登录后再上传')
            return
        if self.clientID < 0:
            self.add_log('当前客户端未注册 请先注册客户端')
            return

        title = self.window.client_title_input.text()
        des = self.window.client_des_input.toPlainText()
        unpress_pwd = self.window.client_unpress_pwd_input.text()
        money = self.window.client_money_input.text()
        file_format = self.file_name.split('.')[-1]
        file_size = 0
        file_size += os.path.getsize(self.file_name)
        if file_size < 1:
            self.add_log('请重新选择要上传的文件 当前可能选择失败')
            return
        file_size = '{}'.format(round(file_size / 1024 / 1024, 5))[:7] + 'MB'
        cate = int(self.window.client_cate_cb.currentText().split('|')[0])

        self.upload_worker = PublistWorker(self.main.cookie, title, des, money, cate, '', unpress_pwd, file_format,
                                           file_size, self.clientID, self.file_name)
        self.upload_worker.pub_finish_signal.connect(self.on_upload_finished)
        self.upload_worker.start()

    def on_upload_finished(self, msg, fid):
        if fid < 0:
            self.add_log('上传失败 原因：{}'.format(msg))
            return
        self.add_log('上传成功：{} 文件ID：{}'.format(msg, fid))

    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.client_log_text.append(str(msg))
        self.window.client_log_text.moveCursor(self.window.client_log_text.textCursor().End)

    def on_check_file_btn_clicked(self):
        self.fid = self.window.file_id_input.text()
        if not self.fid.isdigit():
            self.add_log('文件ID应为数字 当前输入：{}'.format(self.fid))
            return
        self.fid = int(self.fid)
        self.add_log('即将检查:{}'.format(self.fid))
        url = f'{END_POINT}/file/api/file/{self.fid}/'
        self.check_worker = HttpWorker(url, method='GET', cookie=self.main.cookie)
        self.check_worker.finish_signal.connect(self.on_check_file_finished)
        self.check_worker.start()

    def on_check_file_finished(self, res):
        print('on_check_file_finished')
        data = res.json()
        self.file_data = data
        print(data)
        title = data.get('title', '获取失败')
        self.add_log(title)
        self.window.file_title_label.setText(title[:15])

    def on_set_file_download_btn_clicked(self):
        if not self.fid:
            self.add_log('请先点击检测文件可用性按钮')
            return
        if not self.file_name:
            self.add_log('请设置目标文件')
            return
        if self.clientID < 0:
            self.add_log('当前客户端未注册 请先注册客户端')
            return
        print('on_set_file_download_btn_clicked')
        self.file_data['download_url'] = f'CLIENT|{self.clientID}|{self.file_name}'
        if 'main_img' in self.file_data: del self.file_data['main_img']
        if 'tags_str' in self.file_data: del self.file_data['tags_str']
        if 'main_img_url' in self.file_data: del self.file_data['main_img_url']
        if 'file' in self.file_data: del self.file_data['file']
        if 'download_num' in self.file_data: del self.file_data['download_num']
        if 'grade' in self.file_data: del self.file_data['grade']
        if 'c_time' in self.file_data: del self.file_data['c_time']
        if 'creat_user' in self.file_data: del self.file_data['creat_user']
        if 'tags' in self.file_data: del self.file_data['tags']
        self.file_data['state'] = 'checking'
        # print(self.file_data.keys())
        url = f'{END_POINT}/file/api/file/{self.fid}/'
        self.fid = ''
        self.set_file_download_worker = HttpWorker(url, method='POST', data=self.file_data, cookie=self.main.cookie)
        self.set_file_download_worker.finish_signal.connect(self.on_set_file_download_finished)
        self.set_file_download_worker.start()
        self.add_log(f"修改文件{self.file_data['title']} 目标下载地址：{self.file_data['download_url']}")

    def on_set_file_download_finished(self, res):
        data = res.json()
        if data.get('msg'):
            self.add_log(data.get('msg'))
        else:
            self.add_log(f'未知错误：{data}')


if __name__ == '__main__':
    files = ['client.ui', 'data.py']
