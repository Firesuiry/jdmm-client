from lanzou.api import LanZouCloud

final_files = []
final_share_infos = []


def lzy_login(cookies):
    lzy = LanZouCloud()
    cookies = cookies.split()
    cookie_dic = {}
    for cookie in cookies:
        cookie.replace(' ', '')
        cookie.replace(';', '')
        if '=' in cookie:
            kvs = cookie.split('=')
            k = kvs[0]
            v = kvs[1]
            cookie_dic[k] = v
    print(cookie_dic)
    code = lzy.login_by_cookie(cookie_dic)
    print('登录结果', code)
    if code != 0:
        return None
    return lzy


def lzy_get_files(lzy, dir=-1, deepth=9999, path='/', include_dir=False):
    datas = []
    dirs = lzy.get_dir_list(dir)
    files = lzy.get_file_list(dir)
    for file in files:
        data = get_share_info(lzy, file, path)
        datas.append(data)
    if deepth > 1:
        for dir in dirs:
            new_datas = lzy_get_files(lzy, dir.id, deepth - 1, path + dir.name + '/')
            datas += new_datas
            if include_dir:
                datas.append(get_share_info(lzy, dir, path, isdir=True))
    return datas


def get_share_info(lzy, file, path, isdir=False):
    print(file)
    share_info = lzy.get_share_info(file.id)
    print(share_info)
    size = file.size if not isdir else '0 B'
    size_num = float(size.split()[0])
    size_unit = size.split()[1]
    if size_unit == 'K':
        size_num *= 2 ** 10
    if size_unit == 'M':
        size_num *= 2 ** 20

    share_info_dic = {
        'name': file.name,
        'size': size_num,
        'type': file.type if not isdir else '文件夹',
        'isdir': isdir,
        'download_url': share_info.url,
        'tiquma': share_info.pwd,
        'des': path + file.name,
        'parent': path,
    }
    return share_info_dic


def test():
    lzy = lzy_login(cookies)
    datas = lzy_get_files(lzy, include_dir=True)
    for data in datas:
        print(data)


cookies = '''
PHPSESSID=rvglnr9549hoethgdf6q4u2eo2bsv8sq; UM_distinctid=17a3d30f50da50-0d3f2f54a3a955-7a697d6e-1fa400-17a3d30f50e3cf; CNZZDATA1253610888=670235887-1624523794-null|1624523794; _uab_collina=162452425806835047708244; CNZZDATA1253610886=723202744-1624519608-https%3A%2F%2Fup.woozooo.com%2F|1624525021; ylogin=2062551; phpdisk_info=VWNRYwNnVmgGMQJnD2RaCVA0AQoAaFMxATBXNAY5UWIDN1FlBGRWbAM4Vw4OZAQ8WjIDY1kwXDxTMwloUmIDOFU1UWsDaVZqBjQCZw9gWjFQZgE1AGpTMQE1VzMGZVFgAzFRYwRmVmoDNFdjDl0Eb1o/AzNZM1wyU2EJaVJiAzNVZ1Fq; folder_id_c=-1' \
'''
if __name__ == '__main__':
    test()
