from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog
import pathlib
from common import *
import requests
import xlwt
from pathlib import Path
import time

path = Path('./data')
FILE_XLS_FILE = './已发布文件.xls'

class GenerateFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, cookie):
        super().__init__()
        self.cookie = cookie

    def generate_data_xls(self):
        next_url = FILE_QUERY_URL
        book = xlwt.Workbook(encoding="utf-8", style_compression=0)
        sheet = book.add_sheet('test01', cell_overwrite_ok=True)
        sheet.write(0, 0, '标题')
        sheet.write(0, 1, '价格')
        sheet.write(0, 2, '创建时间')
        sheet.write(0, 3, '编号')
        sheet.write(0, 4, '下载地址')
        sheet.write(0, 5, '简介')
        row = 1
        while next_url:
            print(next_url)
            res = requests.get(next_url, cookies=self.cookie)
            data = res.json()
            next_next_url = data.get('next')
            result = data['results']
            if len(result) < 1:
                break
            for file_data in result:
                sheet.write(row, 0, file_data.get('title', ''))
                sheet.write(row, 1, file_data.get('money', 0) / 100)
                sheet.write(row, 2, file_data.get('c_time', ''))
                sheet.write(row, 3, file_data.get('pk', 0))
                sheet.write(row, 4, f"https://www.jiandanmaimai.cn/file/{file_data.get('pk', '')}/")
                sheet.write(row, 5, file_data.get('markdown_describe', ''))
                row += 1
                time.sleep(0.1)
                self.log_signal.emit(f"正在写入第{row}条数据：{file_data.get('title', '')} 编号：{file_data.get('pk', 0)}")

            if next_next_url == next_url:
                break
            else:
                next_url = next_next_url
        book.save(FILE_XLS_FILE)
        self.log_signal.emit(f"已经写入完成 共计{row}条数据")

    def run(self):
        self.log_signal.emit('启动生成所有文件信息列表')
        # if os.path.exists(FILE_XLS_FILE):
        #     self.log_signal.emit(f'当前已有文件 重新生成请删除{FILE_XLS_FILE}')
        #     return

        try:
            self.generate_data_xls()
        except Exception as e:
            print(e)
            self.log_signal.emit(f'出现错误 当前错误：{e}')





class AccountManager:
    def __init__(self, window, main):
        self.window = window
        self.main = main
        self.add_log('欢迎使用账号管理工具')
        self.window.generate_file_xls_btn.clicked.connect(self.on_generate_file_xls_clicked)

    def on_generate_file_xls_clicked(self):
        self.add_log('正在导出所有信息')
        if not self.main.login:
            self.add_log(f'当前未登录 请登录后重试')
            return
        self.generate_file_xls_worker = GenerateFileXlsWorker(self.main.cookie)
        self.generate_file_xls_worker.log_signal.connect(self.add_log)
        self.generate_file_xls_worker.start()

    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.account_info_log_text.append(str(msg))
        self.window.account_info_log_text.moveCursor(self.window.client_log_text.textCursor().End)
