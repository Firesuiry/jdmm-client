from PySide2.QtCore import QThread
from PySide2.QtWidgets import QFileDialog
import pathlib
from common import *
from ftp_server import FtpServer


class FtpServerWorker(QThread):
    def __init__(self,host,path):
        super().__init__()
        self.host = host
        self.path = path

    def run(self):
        server = FtpServer()
        server.start_easy_share_server(self.host, self.path)


class FileTransTool:
    def __init__(self, window):
        self.window = window
        self.set_state('没有指定要分享的文件 请点击下方按钮进行设置')
        self.ipv6host = get_Local_ipv6_address()
        self.window.ipv6Lable.setText(self.ipv6host)
        self.window.filePathLable.setText('无')

        self.window.setShareBtn.clicked.connect(self.on_set_share_file_btn_clicked)

    def on_set_share_file_btn_clicked(self):
        print('设置分享目标文件')
        file_name = QFileDialog.getOpenFileName(self.window, "选择分享的文件", r"C:\Users\Administrator\Desktop")
        print('当前选择文件:{}'.format(file_name))
        if file_name[0] == '':
            return
        file_path = file_name[0]
        self.window.filePathLable.setText(file_path)
        path = pathlib.Path(file_path)
        dir = path.parent
        name = path.name
        print(dir)
        print(name)
        self.ftp_worker = FtpServerWorker(host=self.ipv6host,path=str(dir))
        self.ftp_worker.start()
        self.set_state('已经启动分享服务器')
        url = 'ftp://[{}]/{}'.format(self.ipv6host,name)
        self.window.downloadUrlText.setText(url)


    def set_state(self, msg):
        self.window.fileTransStateLable.setText(msg)
