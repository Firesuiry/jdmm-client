from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtCore import QFile, QThread, Signal
from PySide2.QtGui import QWindow, QKeyEvent
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QItemDelegate, QTableWidgetItem, QMessageBox, QWidget, QHBoxLayout

import requests

from account_manage import AccountManager
from common import check_url
from data import get_key, set_key
from file_server import JdmmFileServer
from multi_uploader import MultiUploadWidget, get_table_content, set_table_content
from prepub_manager import PrepubWidget


class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, QWidget, QStyleOptionViewItem, QModelIndex):
        return None





class LoginWorker(QThread):
    login_finish_signal = Signal(requests.Response)

    def __init__(self, username, pwd):
        super(LoginWorker, self).__init__()
        print('登陆进程创建完成')
        self.username = username
        self.pwd = pwd

    def run(self):
        print('进入登陆进程')
        username = self.username
        pwd = self.pwd
        print('用户名：{}'.format(username))
        print('密码：{}'.format(pwd))

        data = {
            'action': 'login',
            'username': username,
            'password': pwd

        }
        url = 'https://www.jiandanmaimai.cn/account/api/auth/'
        res = requests.post(url, data)
        self.login_finish_signal.emit(res)


class PublistWorker(QThread):
    pub_finish_signal = Signal(requests.Response, int)
    pub_fail_signal = Signal(str, int)

    def __init__(self, table, cookie, cateCb):
        super(PublistWorker, self).__init__()
        self.table = table
        self.cookie = cookie
        self.cateCb = cateCb

    def run(self):
        print('发布进程运行')

        table = self.table
        post_url = 'https://www.jiandanmaimai.cn/file/api/files/'

        for row in range(table.rowCount()):
            pub_id = get_table_content(table, row, 0)

            title = get_table_content(table, row, 1)
            des = get_table_content(table, row, 2)
            url = get_table_content(table, row, 3)
            tiquma = get_table_content(table, row, 4)
            unpress_pwd = get_table_content(table, row, 5)
            money = get_table_content(table, row, 6)
            file_format = get_table_content(table, row, 7)
            file_size = get_table_content(table, row, 8)
            main_img = get_table_content(table, row, 9)
            cate = int(self.cateCb.currentText().split('|')[0])
            if not title:
                continue
            if not des:
                des = title
            if not url or not check_url(url):
                self.pub_fail_signal.emit('网址无效，需要带http(s)前缀且无空格', row)
                continue

            if not money:
                self.pub_fail_signal.emit('没有提供有效价格', row)
                continue

            if '成功' in pub_id:
                continue

            if url == 'PREPUB':
                des += '\r\n本文件为预发布文件，购买后请根据提供的卖家联系方式联系卖家获取本文件'
            data = {
                'title': title,
                'money': int(float(money) * 100),
                'markdown_describe': des,
                'download_url': url,
                'tiquma': tiquma,
                'unzip_password': unpress_pwd,
                'file_format': file_format,
                'file_size': file_size,
                'category': cate
            }
            files = {}
            if main_img:
                f = files['main_img'] = open(main_img, 'rb')
            print(data)
            res = requests.post(post_url, data, cookies=self.cookie, files=files)
            self.pub_finish_signal.emit(res, row)
            if main_img:
                f.close()





class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        ui_file = QFile("client.ui")
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()

        self.window = loader.load(ui_file)
        self.multi_uploader = MultiUploadWidget(self.window, self)

        self.function_connect()
        self.arg_init()
        self.ui_init()

        self.table.installEventFilter(self)

        self.window.show()

        username = get_key('username')
        pwd = get_key('pwd')
        if username:
            self.window.userNameEdit.setText(username)
        if pwd:
            self.window.pwdEdit.setText(pwd)
        if username and pwd:
            self.on_login_btn_clicked()

        self.file_server = JdmmFileServer(self.window, self)
        self.account_manager = AccountManager(self.window, self)
        self.prepub = PrepubWidget(self.window, self)

    def login_btn_process(self, res):
        print('进入登陆信号回调')
        print(res.json())
        print(res.cookies)
        data = res.json()
        self.show_msg(data['msg'])
        if '错误' in data['msg']:
            self.window.stateLable.setText('登陆失败')
        else:
            self.window.stateLable.setText('登陆成功')
            self.cookie = res.cookies
            self.refresh_state()
            self.login = True
            set_key('username', self.username)
            set_key('pwd', self.pwd)
        self.window.loginBtn.setEnabled(True)

        self.file_server.on_login_success()

    def on_publish_single_finish(self, res, row):
        print(res.text)
        data = res.json()
        code = data.get('code')
        if code < 300:
            id = data['detail']['id']
            set_table_content(self.table, row, 0, '发布成功 ID：{}'.format(id))
        else:
            set_table_content(self.table, row, 0, '发布失败 原因：{}'.format(data.get('msg')))

    def on_publish_fail(self, msg, row):
        set_table_content(self.table, row, 0, msg)

    def on_publish_all_finish(self):
        self.window.publishBtn.setEnabled(True)

    def msg_box(self, msg):
        QMessageBox.critical(
            self.window,
            '错误',
            '请选择爬取数据存储路径！')

    def ui_init(self):
        table = self.window.inforTable
        table.setRowCount(10)
        table.setItemDelegateForColumn(self.blockCol, EmptyDelegate(table))  # 设置第二列不可编辑
        table.setColumnWidth(self.blockCol, 280)

    def function_connect(self):
        # 登陆区
        self.window.loginBtn.clicked.connect(self.on_login_btn_clicked)

        # 批量上传区
        self.window.clearBtn.clicked.connect(self.on_clear_btn_clicked)
        self.window.deleteBtn.clicked.connect(self.on_delete_current_btn_clicked)
        self.window.insertBtn.clicked.connect(self.on_addtable_btn_clicked)
        self.window.publishBtn.clicked.connect(self.on_publish_btn_clicked)

    def check_login(self):
        if self.login:
            return True
        url = 'https://www.jiandanmaimai.cn/account/api/auth/'
        res = requests.get(url, cookies=self.cookie)
        data = res.json()
        if data.get('code') == 200:
            return True
        else:
            return False

    def show_msg(self, msg):
        self.window.message_label.setText(str(msg))

    def arg_init(self):
        self.cookie = None
        self.table = self.window.inforTable
        self.login = False
        self.username = ''
        self.pwd = ''
        self.clip = QtWidgets.QApplication.clipboard()
        self.blockCol = 0

    def on_addtable_btn_clicked(self):
        print('点击 增加行数按钮')
        table = self.window.inforTable
        table.insertRow(0)

    def on_clear_btn_clicked(self):
        table = self.window.inforTable
        table.clearContents()

    def on_delete_current_btn_clicked(self):
        table = self.window.inforTable
        currentrow = table.currentRow()
        print(currentrow)
        if currentrow == -1:
            self.show_msg('当前未选择行，无法删除')
            return
        table.removeRow(currentrow)

    def on_publish_btn_clicked(self):
        print('点击发布')
        if self.check_login():
            pass
        else:
            self.show_msg('当前未登录 请登录后再上传')
            return

        self.window.publishBtn.setEnabled(False)

        self.pub_woker = PublistWorker(self.table, self.cookie, self.window.cateCb)
        self.pub_woker.pub_finish_signal.connect(self.on_publish_single_finish)
        self.pub_woker.finished.connect(self.on_publish_all_finish)
        self.pub_woker.pub_fail_signal.connect(self.on_publish_fail)
        self.pub_woker.start()

    def refresh_state(self):
        url = 'https://www.jiandanmaimai.cn/account/api/user/0/'
        res = requests.get(url, cookies=self.cookie)
        print(res.json())
        data = res.json()
        self.window.uidLabel.setText(str(data.get('id', '未登录')))
        self.window.userNameLabel.setText(str(data.get('username', '未登录'))[:10])

    def on_login_btn_clicked(self):
        self.window.loginBtn.setEnabled(False)
        print('尝试登陆')
        self.window.stateLable.setText('正在尝试登陆')
        self.username = self.window.userNameEdit.text()
        self.pwd = self.window.pwdEdit.text()

        self.login_thread = LoginWorker(self.username, self.pwd)
        print('尝试登陆启动进程')
        self.login_thread.login_finish_signal.connect(self.login_btn_process)
        self.login_thread.start()
        print('尝试登陆按键事件结束')

    def copySelection(self):
        selection = self.table.selectedIndexes()
        if selection:
            rows = list(set(sorted(index.row() for index in selection)))
            columns = list(set(sorted(index.column() for index in selection)))

            s = ''
            for row in rows:
                for col in columns:
                    print('行：{}，列：{}'.format(row, col))
                    s += (get_table_content(self.table, row, col) + '\t')
                s += '\n'

            self.clip.setText(s)

    def pasteSelection(self):
        selection = self.table.selectedIndexes()
        if selection:
            buffer = self.clip.text()
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            base_row = rows[0]
            base_col = columns[0]
            for row_content in buffer.split('\n'):
                col = base_col
                for col_content in row_content.split('\t'):
                    set_table_content(self.table, base_row, col, col_content, self.blockCol)
                    col += 1
                base_row += 1

    def keyPressEvent(self, e):
        print('进入键盘事件组')
        if (e.modifiers() & QtCore.Qt.ControlModifier):
            if e.key() == QtCore.Qt.Key_C:  # copy
                self.copySelection()
            elif e.key() == QtCore.Qt.Key_V:
                self.pasteSelection()

    def eventFilter(self, obj, event):
        # print('进入事件过滤器:{}'.format(event))
        if (type(event) == QKeyEvent):
            if event.key() == QtCore.Qt.Key_C:  # copy
                print('ctrl c事件')
                self.copySelection()
            elif event.key() == QtCore.Qt.Key_V:
                print('ctrl v事件')
                self.pasteSelection()

        return super().eventFilter(obj, event)


if __name__ == '__main__':
    print('开始执行')
    app = QApplication([])
    try:
        mainWindow = MainWindow()
    except Exception as e:
        print(e)
        input()
    print('程序运行结束 返回值：{}'.format(app.exec_()))
