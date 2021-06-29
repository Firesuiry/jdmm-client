import os
import pathlib
import re
import time
import openpyxl
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QFileDialog

from common import cal_md5, write_xlsx, has_chinese
import sqlite3

from utils.lanzouyun import lzy_login, lzy_get_files

FILE_XLS_FILE = './要发布文件.xlsx'


class GenerateLzyXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, cookie, config):
        super().__init__()
        self.cookie = cookie
        self.config = config
        self.values = []
        self.lzy_client = None

    def run(self) -> None:
        self.log_signal.emit('程序开始执行，请勿操作以免卡死')
        self.log_signal.emit('开始登录')
        self.lzy_client = lzy_login(self.cookie)
        if self.lzy_client is None:
            self.log_signal.emit('蓝奏云登录失败')
            return
        self.values = lzy_get_files(self.lzy_client, include_dir=(not self.config.get('filter_dir')), dir_name_filter=self.config.get('dir_limit'))
        self.log_signal.emit('获取{}条数据 开始写入' .format(len(self.values)))
        try:
            self.generate_data_xls()
        except PermissionError:
            self.log_signal.emit(f'出现错误 请手动删除 要发布文件.xls 或者关闭wps或excel')
        except Exception as e:
            self.log_signal.emit(f'出现错误 {e}')


    def generate_data_xls(self):
        print('generate_data_xls')
        titles = ['标题', '描述', '网盘链接', '网盘提取码', '解压密码', '价格', '文件类型', '文件大小']
        write_datas = []
        for data in self.values:
            write_data = ['' for _ in range(9)]
            write_data[0] = file_title = data['name']
            write_data[1] = file_des = f"文件标题：{data['des']}"
            write_data[2] = file_url = data['download_url']
            write_data[3] = data['tiquma']
            write_data[5] = prize = '1'
            write_data[6] = file_type = data['type']
            write_data[7] = file_size = '{:.2f}MB'.format(data['size'] / 2 ** 20)
            res = file_check(file_name=file_title, file_size=data['size'], is_dir=data['isdir'], config=self.config,
                             source='PAN',
                             parent_dir=data['parent'])
            if res:
                write_datas.append(write_data)

        write_xlsx(titles, write_datas, '要发布文件.xlsx', add=self.config['add'])
        self.log_signal.emit(f"已经写入完成 共计{len(write_datas)}条数据")
        self.log_signal.emit(f"请查看上方的介绍完成下一步发布")


class GenerateBaiduPanFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, dbpath, config):
        super().__init__()
        self.dbpath = dbpath
        self.config = config
        self.values = []

    def run(self):
        self.log_signal.emit('程序开始执行，请勿操作以免卡死')
        self.log_signal.emit('开始读取百度网盘文件数据库')
        self.export_baidupan_file_info()
        self.log_signal.emit('数据库读取完成，共计{}条数据'.format(len(self.values)))
        self.log_signal.emit('开始写入数据')
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
        cursor.execute('select server_filename,file_size,md5,parent_path,isdir from cache_file ORDER BY parent_path')

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
            write_data = ['' for _ in range(9)]
            write_data[0] = file_title = data[0]
            write_data[1] = file_des = f"文件标题：{data[3]}{data[0]}"
            write_data[2] = file_url = 'PREPUB'
            write_data[5] = prize = '1'
            write_data[6] = file_type = data[0].split('.')[-1] if '.' in data[0] else ''
            write_data[7] = file_size = '{:.2f}MB'.format(data[1] / 2 ** 20)
            res = file_check(file_name=file_title, file_size=data[1], is_dir=data[4], config=self.config, source='PAN',
                             parent_dir=data[3])
            if res:
                write_datas.append(write_data)

        write_xlsx(titles, write_datas, '要发布文件.xlsx', add=self.config['add'])
        self.log_signal.emit(f"已经写入完成 共计{len(write_datas)}条数据")
        self.log_signal.emit(f"请查看上方的介绍完成下一步发布")


class GenerateFileXlsWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, dir_name, config):
        super().__init__()
        self.dir_name = dir_name
        self.datas = []
        self.config = config

    def add_file_info(self, path, search_depth):
        path = pathlib.Path(path)
        files = path.glob('*')
        for file in files:
            if os.path.isdir(file):
                if search_depth > 1:
                    self.add_file_info(file, search_depth - 1)
            name = file.name
            size = os.path.getsize(file)
            data = {
                'size': size,
                'name': name,
                'type': name.split('.')[-1][:5] if '.' in name else '',
                'isdir': os.path.isdir(file),
                'parent': file.parent
            }
            self.datas.append(data)

    def generate_data_xls(self):
        titles = ['标题', '描述', '网盘链接', '网盘提取码', '解压密码', '价格', '文件类型', '文件大小']
        write_datas = []
        for data in self.datas:
            write_data = ['' for _ in range(9)]
            write_data[0] = data.get('name', '')
            write_data[1] = f"{data.get('parent')}\\{data.get('name', '')}"
            write_data[2] = 'PREPUB'
            write_data[5] = '1'
            write_data[6] = data.get('type', '')
            write_data[7] = '{:.2f}MB'.format(data.get('size', 0) / 2 ** 20)
            res = file_check(file_name=write_data[0], file_size=data.get('size', 0), is_dir=data.get('isdir', ''),
                             config=self.config,
                             source='LOCAL',
                             parent_dir='')
            if res:
                write_datas.append(write_data)

        write_xlsx(titles, write_datas, '要发布文件.xlsx', add=self.config.get('add'))
        self.log_signal.emit(f"已经写入完成 共计{len(write_datas)}条数据")
        self.log_signal.emit(f"请查看上方的介绍完成下一步发布")

    def run(self):
        self.log_signal.emit('启动生成预发布文件')
        dir_search_depth = int(self.config['dir_search_depth'])
        self.datas.clear()
        self.log_signal.emit(f'启动生成  请稍后 搜索深度：{dir_search_depth}')
        self.add_file_info(self.dir_name, dir_search_depth)
        self.log_signal.emit(f'文件读取完成 共读取到{len(self.datas)}条数据')
        try:
            self.generate_data_xls()
        except PermissionError:
            self.log_signal.emit(f'出现错误 请手动删除 要发布文件.xls 或者关闭wps或excel')
        except Exception as e:
            print(e)
            self.log_signal.emit(f'出现错误 当前错误：{e}')


class PrepubWidget:
    def __init__(self, window, main):
        self.window = window
        self.main = main

        self.window.select_prepub_file_btn.clicked.connect(self.process_directory)
        self.window.select_baidupan_out_file.clicked.connect(self.process_baidupan_db_file)
        self.window.lzyStartGenerateBtn.clicked.connect(self.lanzouyun_start_generate)

    def lanzouyun_start_generate(self):
        self.add_log('开始执行蓝奏云文件预分享')
        lzy_cookie = self.window.LzyCookieTextEdit.toPlainText()
        self.add_log(lzy_cookie)
        if 'ylogin' not in lzy_cookie or 'phpdisk_info' not in lzy_cookie:
            self.add_log('cookie有错 没有包含ylogin和phpdisk_info')
            return
        config = self.get_config()

        self.lzypan_prepub = GenerateLzyXlsWorker(cookie=lzy_cookie, config=config)
        self.lzypan_prepub.log_signal.connect(self.add_log)
        self.lzypan_prepub.start()

    def process_directory(self):
        config = self.get_config()
        self.add_log('开始执行本地文件预分享，文件夹选择，请稍等')
        dir_name = QFileDialog.getExistingDirectory(self.window, "选择要分享的文件夹", r"C:\Users\Administrator\Desktop")
        self.add_log('当前选择的文件夹：')
        self.add_log(dir_name)

        self.local_prepub = GenerateFileXlsWorker(dir_name, config)
        self.local_prepub.log_signal.connect(self.add_log)
        self.local_prepub.start()

    def process_baidupan_db_file(self):
        config = self.get_config()
        self.add_log('开始执行百度网盘文件预分享，请稍等')
        file_names = QFileDialog.getOpenFileName(self.window, "选择分享的文件", r"C:\Users\Administrator\Desktop",
                                                 '网盘文件目录(BaiduYunCacheFileV0.db)')
        file_name = file_names[0]
        self.add_log('当前选择的文件：')
        self.add_log(file_name)

        self.baidupan_prepub = GenerateBaiduPanFileXlsWorker(file_name, config)
        self.baidupan_prepub.log_signal.connect(self.add_log)
        self.baidupan_prepub.start()

    def add_log(self, msg):
        print('添加log：{}'.format(msg))
        self.window.prepub_text.append(str(msg))
        self.window.prepub_text.moveCursor(self.window.client_log_text.textCursor().End)

    def get_config(self):
        dir_search_depth = self.window.dir_search_depth_edit.text()
        min_file_limit = self.window.min_file_limit_edit.text()
        dir_limit = self.window.dir_limit_edit.text()
        re_str = self.window.re_str_edit.text()
        filter_dir = self.window.filter_dir_Cb.isChecked()
        add = self.window.add_cb.isChecked()
        filter_chinese = self.window.filter_chinese_cb.isChecked()
        if not dir_search_depth.isdigit():
            self.add_log('深度信息必须是数字')
            return
        if not min_file_limit.isdigit():
            self.add_log('文件最小大小必须是数字')
            return
        if re_str:
            try:
                re_pattern = re.compile(re_str)
            except Exception as e:
                self.add_log('正则匹配项编译失败 原因：{}'.format(e))
                return
        config = locals().copy()
        del config['self']
        return config


def file_check(file_name, file_size, is_dir, config, source='LOCAL', parent_dir=''):
    min_file_limit = float(config['min_file_limit'])
    if file_size < min_file_limit * 2 ** 10 and not is_dir:
        return False
    dir_limit = config['dir_limit']
    if source == 'PAN' and dir_limit not in (parent_dir + file_name):
        return False
    re_pattern = config.get('re_pattern')
    if re_pattern and len(re_pattern.findall(file_name)) < 1:
        return False
    if config.get('filter_dir') and is_dir:
        return False
    if config.get('filter_chinese') and not has_chinese(file_name):
        return False
    return True


if __name__ == '__main__':
    print('start')
    dbpath = r'C:\Users\Administrator\AppData\Roaming\baidu\BaiduNetdisk\users\eabe70b53624ca13c9dcabe2da9c573a\BaiduYunCacheFileV0.db'
    p = GenerateBaiduPanFileXlsWorker(dbpath)
    p.run()
