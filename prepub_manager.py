import os
import pathlib
import time
import openpyxl
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog

from common import cal_md5, write_xlsx
import sqlite3

FILE_XLS_FILE = './要发布文件.xlsx'


class GenerateBaiduPanFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, dbpath):
        super().__init__()
        self.dbpath = dbpath
        self.values = []

    def run(self):
        self.export_baidupan_file_info()
        self.generate_data_xls()
        return
        try:
            self.generate_data_xls()
        except PermissionError:
            self.log_signal.emit(f'出现错误 请手动删除 要发布文件.xls 或者关闭wps或excel')
        except Exception as e:
            self.log_signal.emit(f'出现错误 {e}')

    def export_baidupan_file_info(self):
        print('export_baidupan_file_info')
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        # 执行查询语句：
        cursor.execute('select server_filename,file_size,md5,parent_path from cache_file')

        # 使用featchall获得结果集（list）
        values = cursor.fetchall()
        # for value in values:
        #     print(value)
        self.values = values
        return values

    def generate_data_xls(self):
        print('generate_data_xls')
        titles = ['标题', '描述', '网盘链接', '网盘提取码', '解压密码', '价格', '文件类型', '文件大小']
        write_datas = []
        for data in self.values:
            size = data[1]
            # if size < 2 ** 0:
            #     continue
            write_data = ['' for _ in range(9)]
            write_data[0] = file_title = data[0]
            write_data[1] = file_des = f"文件标题：{data[3]}{data[0]}"
            write_data[2] = file_url = 'PREPUB'
            write_data[4] = prize = '1'
            write_data[6] = file_type = data[0].split('.')[-1] if '.' in data[0] else ''
            write_data[7] = file_size = '{:.2f}MB'.format(data[1] / 2 ** 20)
            write_datas.append(write_data)

        write_xlsx(titles, write_datas, '要发布文件.xlsx')
        self.log_signal.emit(f"已经写入完成 共计{len(self.values)}条数据")
        self.log_signal.emit(f"请查看上方的介绍完成下一步发布")


class GenerateFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, datas):
        super().__init__()
        self.datas = datas

    def generate_data_xls(self):
        titles = ['标题', '描述', '网盘链接', '网盘提取码', '解压密码', '价格', '文件类型', '文件大小']
        write_datas = []
        for data in self.datas:
            write_data = ['' for _ in range(9)]
            write_data[0] = data.get('name', '')
            write_data[1] = f"文件标题：{data.get('name', '')}"
            write_data[2] = 'PREPUB'
            write_data[5] = '1'
            write_data[6] = data.get('type', '')
            write_data[7] = data.get('size', '')
            write_datas.append(write_data)

        write_xlsx(titles, write_datas, '要发布文件.xlsx')
        self.log_signal.emit(f"已经写入完成 共计{len(self.datas)}条数据")
        self.log_signal.emit(f"请查看上方的介绍完成下一步发布")

    def run(self):
        self.log_signal.emit('启动生成预发布文件')

        try:
            self.generate_data_xls()
        except PermissionError:
            self.log_signal.emit(f'出现错误 请手动删除 要发布文件.xls 或者关闭wps或excel')
        except Exception as e:
            print(e)
            self.log_signal.emit(f'出现错误 当前错误：{e}')


def export_file_info(path, md5info=False):
    path = pathlib.Path(path)
    files = path.glob('*')
    datas = []
    for file in files:
        if os.path.isdir(file):
            continue
        name = file.name
        size = os.path.getsize(file)
        md5 = cal_md5(path) if md5info else ''
        data = {
            'size': '{:.2f}MB'.format(size / 2 ** 20),
            'name': name,
            'md5': md5,
            'type': name.split('.')[-1][:5] if '.' in name else ''
        }
        if size < 1024 or '.' not in name:
            continue
        datas.append(data)
    print(datas)
    return datas


class PrepubWidget:
    def __init__(self, window, main):
        self.window = window
        self.main = main

        self.window.select_prepub_file_btn.clicked.connect(self.process_directory)
        self.window.select_baidupan_out_file.clicked.connect(self.process_baidupan_db_file)

    def process_directory(self):
        self.add_log('开始执行本地文件预分享，文件夹选择，请稍等')
        dir_name = QFileDialog.getExistingDirectory(self.window, "选择要分享的文件夹", r"C:\Users\Administrator\Desktop")
        self.add_log('当前选择的文件夹：')
        self.add_log(dir_name)

        datas = export_file_info(dir_name)

        self.local_prepub = GenerateFileXlsWorker(datas)
        self.local_prepub.log_signal.connect(self.add_log)
        self.local_prepub.run()

    def process_baidupan_db_file(self):
        self.add_log('开始执行百度网盘文件预分享，请稍等')
        file_names = QFileDialog.getOpenFileName(self.window, "选择分享的文件", r"C:\Users\Administrator\Desktop",
                                                 '网盘文件目录(BaiduYunCacheFileV0.db)')
        file_name = file_names[0]
        self.add_log('当前选择的文件：')
        self.add_log(file_name)

        self.baidupan_prepub = GenerateBaiduPanFileXlsWorker(file_name)
        self.baidupan_prepub.log_signal.connect(self.add_log)
        self.baidupan_prepub.run()

    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.prepub_text.append(str(msg))
        self.window.prepub_text.moveCursor(self.window.client_log_text.textCursor().End)


if __name__ == '__main__':
    print('start')
    dbpath = r'C:\Users\Administrator\AppData\Roaming\baidu\BaiduNetdisk\users\eabe70b53624ca13c9dcabe2da9c573a\BaiduYunCacheFileV0.db'
    p = GenerateBaiduPanFileXlsWorker(dbpath)
    p.run()
