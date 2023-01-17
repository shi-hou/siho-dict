import json
from retry import retry

from core import utils

'''====================================================百度翻译===================================================='''

URL_BAIDU_LANG_DETECT = 'https://fanyi.baidu.com/langdetect'
URL_BAIDU_TRANS_V1 = 'https://fanyi.baidu.com/transapi'
URL_BAIDU_TTS = 'https://fanyi.baidu.com/gettts'


def baidu_lang_detect(text):
    return utils.request_post(URL_BAIDU_LANG_DETECT, json={'query': text}).json()['lan']


@retry(tries=3)
def baidu_trans(text, _) -> dict:
    # 非中文->中文, 中文(也可能是日文)->英文
    from_lang = baidu_lang_detect(text)
    to_lang = 'zh' if from_lang != 'zh' else 'en'
    resp = utils.request_post(URL_BAIDU_TRANS_V1, json={
        'from': from_lang,
        'to': to_lang,
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    return_body = None
    if resp_type == 1:
        return_body = {'type': 1, 'text': text}
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None and from_lang == 'en':
            return_body['voice'] = [{
                'pron': f"英{voice[0]['en_phonic']}",
                'url': f'https://fanyi.baidu.com/gettts?lan=uk&text={text}&spd=3&source=web'
            }, {
                'pron': f"美{voice[1]['us_phonic']}",
                'url': f'https://fanyi.baidu.com/gettts?lan=en&text={text}&spd=3&source=web'
            }]
        mean = result['content'][0]['mean']
        return_body['pre'] = []
        for m in mean:
            return_body['pre'].append({
                'title': m.get('pre', ''),
                'trans': m.get('cont')
            })

    elif resp_type == 2:
        return_body = {
            'type': 2,
            'text': text,
            'trans': resp['data'][0]['dst']
        }
    return return_body


'''====================================================Moji辞書===================================================='''

URL_MOJI_LOGIN = 'https://api.mojidict.com/parse/login'
URL_MOJI_SEARCH_V3 = 'https://api.mojidict.com/parse/functions/search_v3'
URL_MOJI_FETCH_WORDS = 'https://api.mojidict.com/parse/functions/fetchManyWords'
URL_MOJI_FETCH_TTS = 'https://api.mojidict.com/parse/functions/tts-fetch'

_ClientVersion = 'js2.12.0'
_ApplicationId = 'E62VyFVLMiW7kvbtVq3p'
_InstallationId = '7d959a18-48c4-243c-7486-632147466544'
g_os = 'PCWeb'
g_ver = 'v4.4.1.20221229'


@retry(tries=3)
def moji_login(email: str, password: str):
    return utils.request_post(URL_MOJI_LOGIN, json={
        "username": email,
        "password": password,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "_InstallationId": _InstallationId
    }).json().get('sessionToken')


# moji_account = utils.get_config().get('moji-account')
# _SessionToken = moji_login(moji_account.get('email'), moji_account.get('password'))


@retry(tries=3, delay=1)
def moji_search(text, _) -> dict:
    search_results = utils.request_post(URL_MOJI_SEARCH_V3, json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "langEnv": "zh-CN_ja",
        "searchText": text
    }).json().get('result').get('searchResults')

    if len(search_results) == 0:
        return {}

    word_id = search_results[0].get('tarId')
    return moji_fetch_word(word_id)


@retry(tries=3)
def moji_fetch_word(word_id: str):
    result = utils.request_post(URL_MOJI_FETCH_WORDS, json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "wordIds": [word_id],
        "skipAccessories": False,
        "auth": False
    }).json().get('result').get('result').get(word_id)
    word = result.get('word')
    tts_url = moji_tts_url(word_id, 102)
    result_body = {
        'type': 1,
        'text': word.get('spell'),
        'voice': [{
            'pron': word.get('pron', '') + word.get('accent', ''),
            'url': tts_url
        }]
    }
    pre = []
    pre_id_map_pre_index = {}
    for index, detail in enumerate(result.get('details')):
        pre.append({
            'title': detail.get('title').replace('#', '・'),
            'trans': []
        })
        pre_id_map_pre_index[detail.get('objectId')] = index
    for subdetail in result.get('subdetails'):
        index = pre_id_map_pre_index.get(subdetail.get('detailsId'))
        if index is not None:
            pre[index]['trans'].append(subdetail.get('title'))
    result_body['pre'] = pre
    return result_body


@retry(tries=3)
def moji_tts_url(tarId: str, tarType: int):
    return utils.request_post(URL_MOJI_FETCH_TTS, json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "tarId": tarId,
        "tarType": tarType,
        "voiceId": "f000"
    }).json().get('result').get('result').get('url')


'''====================================================词典列表===================================================='''
'''
翻译返回数据结构体

单词:
{
    type: 1
    text: 'word', 
    voice: [
        {
            pron: 'xx', # 音标/假名
            url: 'url'
        },
        {
            pron: 'xx', 
            url: 'url'
        },
    ], 
    pre: [  # 词性
            {
                title: 'n', 
                trans: ['xx', 'yy', 'zz']   # 释义list
            },
            {
                title: 'v', 
                trans: [...]
            }
    ]
}

句子:
{
    type: 2
    text: 'xxx yyy zzz', 
    trans: '喔喔喔喔'
}
'''
dict_list = [
    {
        'name': 'baidu-v1',
        'able': True,
        'title': '百度翻译',
        'lang': ['all'],  # 'zh':中文, 'en': 英文, 'ja': 日文, 'all': 任意
        'icon': 'baidu-trans-logo.png',
        'audio-icon': 'audio-blue.svg',
        'delimiter': ';',  # 同一词性中各个释义之间的连接符
        'func': baidu_trans,  # 函数参数为(text, from_lang), 即原文和原文语种, 返回为dict类型, 结构见上
    },
    {
        'name': 'moji-search',
        'able': True,
        'title': 'Moji辞書',
        'lang': ['zh', 'ja'],
        'icon': 'moji-dict-logo.png',
        'audio-icon': 'moji-voice.webp',
        'delimiter': '\n',
        'func': moji_search,
    }
]


class Dicts:
    """
    用于维护词典列表
    """

    def __init__(self):
        self.all_dict = []
        self.on_dict = []
        self.dict_settings = utils.get_config().get('dict', {dict_list[0]['name']: {'on': True}})
        self.resetDict()

    def resetDict(self):
        self.all_dict = []
        self.on_dict = []
        for d in dict_list:
            name = d.get('name')
            able = d.get('able', False)
            on = able and self.dict_settings.get(name, {}).get("on", False)
            title = d.get('title')
            lang = d.get('lang')
            icon = d.get('icon')
            audio_icon = d.get('audio-icon')
            delimiter = d.get('delimiter', ';')
            func = d.get('func')
            dictionary = Dict(name, able, on, title, lang, icon, audio_icon, delimiter, func)
            self.all_dict.append(dictionary)
            if on:
                self.on_dict.append(dictionary)

    def setOn(self, index: int, on: bool):
        dict_name = self.all_dict[index].name
        one_dict_setting = self.dict_settings.get(dict_name, {})
        one_dict_setting['on'] = on
        self.dict_settings[dict_name] = one_dict_setting
        utils.update_config({'dict': self.dict_settings})
        self.resetDict()


class Dict:
    def __init__(self, name: str, able: bool, on: bool, title: str, lang: list, icon: str, audio_icon: str,
                 delimiter: str = ';', func=None):
        self.name = name
        self.able = able
        self.on = on
        self.title = title
        self.lang = lang
        self.icon = icon
        self.audio_icon = audio_icon
        self.delimiter = delimiter
        self.func = func

    @classmethod
    def message_result(cls, text: str):
        return {
            'type': 2,
            'text': text,
            'trans': ''
        }

    def do_trans(self, text, from_lang) -> dict:
        if not self.able or self.func is None:
            return self.message_result('该词典暂不可用')
        if from_lang not in self.lang and 'all' not in self.lang:
            return self.message_result('该词典不支持该语言')

        return self.func(text, from_lang)


# 用于获取所有词典和已开启词典列表
dicts = Dicts()
