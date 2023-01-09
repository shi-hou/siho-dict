import winreg

import requests

__INTERNET_SETTINGS = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,
                                       r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                                       0, winreg.KEY_ALL_ACCESS)


def dict_get(dict_object: dict, key: str, default_value=None):
    try:
        return dict_object[key]
    except:
        return default_value


def is_open_proxy_form_win() -> bool:
    """判断是否开启了代理"""
    try:
        if winreg.QueryValueEx(__INTERNET_SETTINGS, 'ProxyEnable')[0] == 1:
            return True
    except FileNotFoundError as err:
        print('没有找到代理信息：' + str(err))
    except Exception as err:
        print('有其他报错：' + str(err))
    return False


def get_server_form_win() -> str:
    """获取代理配置的url"""
    if is_open_proxy_form_win():
        try:
            return winreg.QueryValueEx(__INTERNET_SETTINGS, 'ProxyServer')[0]
        except FileNotFoundError as err:
            print('没有找到代理信息：' + str(err))
        except Exception as err:
            print('有其他报错：' + str(err))
    else:
        print('系统没有开启代理')
    return ''


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
}


def get_proxies():
    if not is_open_proxy_form_win():
        return None
    url = get_server_form_win()
    return {'https': url} if url else None


def post(url, data=None, json=None):
    return requests.post(url, data, json, headers=headers, proxies=get_proxies())


if __name__ == '__main__':
    pass
