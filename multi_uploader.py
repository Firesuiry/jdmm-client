import requests
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QWidget, QFileDialog, QTableWidgetItem
from common import END_POINT


class InitCateCbWorker(QThread):
    init_finish_signal = Signal(requests.Response)

    def __init__(self):
        super(InitCateCbWorker, self).__init__()

    def run(self):
        res = requests.get(f'{END_POINT}/file/api/category/')
        self.init_finish_signal.emit(res)


class MultiUploadWidget():
    def __init__(self, window, main):
        self.window = window
        self.main = main
        self.init_cate_cb()
        self.window.setMainImgBtn.clicked.connect(self.on_set_main_img_btn_clicked)

    def init_cate_cb(self):
        self.worker = InitCateCbWorker()
        self.worker.init_finish_signal.connect(self.on_init_finished)
        self.worker.start()

    def on_init_finished(self, res: requests.Response):
        datas = res.json()
        pk_date = {}
        for data in datas:
            pk_date[data['pk']] = data
        cbox = self.window.cateCb
        cbox2 = self.window.client_cate_cb
        for data in datas:
            s = '{}|'.format(data['pk'])
            parentid = data.get('parent_category')
            parent_s = '-{}'.format(data['name'])
            while (parentid):
                parent = pk_date[parentid]
                parent_s = '-{}'.format(parent['name']) + parent_s
                parentid = parent.get('parent_category')
            cbox.addItem(s + parent_s)
            cbox2.addItem(s + parent_s)

    def on_set_main_img_btn_clicked(self):
        table = self.window.inforTable
        currentrow = table.currentRow()
        print(currentrow)
        if currentrow == -1:
            self.main.show_msg('当前未选择行，无法设置主图')
            return
        file_names = QFileDialog.getOpenFileName(self.window, "选择分享的文件", r".",
                                                 "图片(*.jpg;*.png;*.bmp)")
        file_name = file_names[0]
        set_table_content(self.main.table, currentrow, 9, file_name)


def get_table_content(table, row, colum):
    thing = table.item(row, colum)
    if thing:
        return thing.text()
    else:
        return ''


def set_table_content(table, row, colum, content, block_col=-1):
    print('设置表格内容 行：{} 列：{} 内容：{}'.format(row, colum, content))
    if colum == block_col:
        return
    item = QTableWidgetItem()
    item.setText(content)
    table.setItem(row, colum, item)
