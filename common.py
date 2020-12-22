import hashlib
import os
import re
import subprocess
import uuid

HEAD_STRUCT = bytes('128sIq32s',encoding='utf-8')
FILE_UPLOAD_URL = 'https://www.jiandanmaimai.cn/file/api/files/'
CLIENT_INFO_URL = 'https://www.jiandanmaimai.cn/file/api/client/'
FILE_QUERY_URL = 'https://www.jiandanmaimai.cn/file/api/files/?self=True&limit=20'


url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
def check_url(url):
    return re.match(url_regex, url) is not None

def cal_md5(file_path):
    with open(file_path, 'rb') as fr:
        md5 = hashlib.md5()
        md5.update(fr.read())
        md5 = md5.hexdigest()
        return md5


def get_file_info(file_path):
    file_name = os.path.basename(file_path)
    file_name_len = len(file_name)
    file_size = os.path.getsize(file_path)
    md5 = cal_md5(file_path)
    return file_name, file_name_len, file_size, md5


def get_Local_ipv6_address():
    child = subprocess.Popen("ipconfig", shell=True, stdout=subprocess.PIPE)
    out = child.communicate();  # 保存ipconfig中的所有信息

    ipv6_pattern = '(([a-f0-9]{1,4}:){7}[a-f0-9]{1,4})'
    try:
        m = re.findall(ipv6_pattern, str(out))
        address = m[1][0]
        print('获取到IPV6地址：{}'.format(address))
        return address
    except Exception as e:
        print(e)
        return

def get_MAC():
    mac = uuid.uuid1().hex[-12:].upper()
    print('当前主机MAC地址为：{}'.format(mac))
    return mac
