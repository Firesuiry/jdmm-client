from lanzou.api import LanZouCloud
import urllib.parse

final_files = []
final_share_infos = []


def lzy_login(cookies):
    lzy = LanZouCloud()
    cookie_dic = cookie_to_dic(cookies)
    print(cookie_dic)
    cookies = {
        'ylogin': cookie_dic['ylogin'],
        'phpdisk_info': urllib.parse.quote(cookie_dic['phpdisk_info'])
    }
    print(cookies)
    code = lzy.login_by_cookie(cookies)

    print('登录结果', code)
    if code != 0:
        return None
    return lzy


def cookie_to_dic(mycookie):
    dic = {}
    for i in mycookie.split('; '):
        dic[i.split('=', 1)[0]] = i.split('=', 1)[1]
    return dic


def lzy_get_files(lzy, dir=-1, deepth=9999, path='/', include_dir=False, dir_name_filter=''):
    print(f'lzy_get_files {locals()}')
    datas = []
    if dir_name_filter and dir_name_filter not in path.split('/'):
        print(f'跳过当前目录 {path}')
    else:
        files = lzy.get_file_list(dir)
        for file in files:
            data = get_share_info(lzy, file, path)
            datas.append(data)
    if deepth > 1:
        dirs = lzy.get_dir_list(dir)
        for dir in dirs:
            new_datas = lzy_get_files(lzy, dir.id, deepth - 1, path + dir.name + '/', include_dir=include_dir,
                                      dir_name_filter=dir_name_filter)
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
    lzy = lzy_login(cookies.replace('\n',''))
    # datas = lzy_get_files(lzy, include_dir=True)
    # for data in datas:
    #     print(data)


cookies = '''
'''


if __name__ == '__main__':
    test()
