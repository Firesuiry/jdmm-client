import requests
from PySide2.QtCore import QThread, Signal
from PySide2.QtWidgets import QWidget


class InitCateCbWorker(QThread):
    init_finish_signal = Signal(requests.Response)

    def __init__(self):
        super(InitCateCbWorker, self).__init__()

    def run(self):
        res = requests.get('http://www.jiandanmaimai.cn/file/api/category/')
        self.init_finish_signal.emit(res)


class MultiUploadWidget():
    def __init__(self, window):
        self.window = window
        self.init_cate_cb()

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
