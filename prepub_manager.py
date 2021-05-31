import os
import pathlib

import xlwt
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog

from common import cal_md5

FILE_XLS_FILE = './要发布文件.xls'


class GenerateFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, datas):
        super().__init__()
        self.datas = datas

    def generate_data_xls(self):
        book = xlwt.Workbook(encoding="utf-8", style_compression=0)
        sheet = book.add_sheet('test01', cell_overwrite_ok=True)
        sheet.write(0, 0, '标题')
        sheet.write(0, 1, '描述')
        sheet.write(0, 2, '网盘链接')
        sheet.write(0, 3, '网盘提取码')
        sheet.write(0, 4, '解压密码')
        sheet.write(0, 5, '价格')
        sheet.write(0, 6, '文件类型')
        sheet.write(0, 7, '文件大小')
        row = 1
        for data in self.datas:
            sheet.write(row, 0, data.get('name', ''))
            sheet.write(row, 1, f"文件标题：{data.get('name', '')}")
            sheet.write(row, 2, 'PREPUB')
            sheet.write(row, 5, '1')
            sheet.write(row, 6, data.get('type', ''))
            sheet.write(row, 7, data.get('size', ''))
            self.log_signal.emit(f"正在写入第{row}条数据：{data.get('name', '')}")
            row += 1

        book.save(FILE_XLS_FILE)
        self.log_signal.emit(f"已经写入完成 共计{row}条数据")
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

    def process_directory(self):
        self.add_log('开始执行本地文件预分享，文件夹选择')
        dir_name = QFileDialog.getExistingDirectory(self.window, "选择要分享的文件夹", r"C:\Users\Administrator\Desktop")
        self.add_log('当前选择的文件夹：')
        self.add_log(dir_name)

        datas = export_file_info(dir_name)

        self.local_prepub = GenerateFileXlsWorker(datas)
        self.local_prepub.log_signal.connect(self.add_log)
        self.local_prepub.run()


    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.prepub_text.append(str(msg))
        self.window.prepub_text.moveCursor(self.window.client_log_text.textCursor().End)


if __name__ == '__main__':
    datas = export_file_info(r'H:\cassann_data0409')
    gfxls = GenerateFileXlsWorker(datas)
    gfxls.run()
