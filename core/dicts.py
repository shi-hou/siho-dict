import json
from retry import retry

from core import utils

'''====================================================百度翻译===================================================='''

URL_BAIDU_LANG_DETECT = 'https://fanyi.baidu.com/langdetect'
URL_BAIDU_TRANS_V1 = 'https://fanyi.baidu.com/transapi'
URL_BAIDU_TTS = 'https://fanyi.baidu.com/gettts'


def baidu_lang_detect(text):
    return utils.request_post(URL_BAIDU_LANG_DETECT, json={'query': text}).json()['lan']


def baidu_trans(text, _) -> dict:
    from_lang = baidu_lang_detect(text)
    # 非中文->中文, 中文(也可能是日文)->英文
    to_lang = 'zh' if from_lang != 'zh' else 'en'
    resp = utils.request_post(URL_BAIDU_TRANS_V1, json={
        'from': from_lang,
        'to': to_lang,
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    result_body = {'text': text}
    if resp_type == 1:
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None and from_lang == 'en':
            result_body['pron_uk'] = voice[0]['en_phonic']
            result_body['voice_uk'] = f'[sound:https://fanyi.baidu.com/gettts?lan=uk&text={text}&spd=3&source=web]'
            result_body['pron_us'] = voice[1]['us_phonic']
            result_body['voice_us'] = f'[sound:https://fanyi.baidu.com/gettts?lan=en&text={text}&spd=3&source=web]'
        trans = ''
        for mean in result['content'][0]['mean']:
            trans += f'''<div class="pos">{mean.get('pre', '')}</div>'''
            trans += f'''<div class="trans">{';'.join(mean.get('cont'))}</div>'''
    else:  # elif resp_type == 2:
        trans = f'''<div>{resp['data'][0]['dst']}</div>'''
    result_body['trans'] = trans
    return result_body


'''====================================================Moji辞書===================================================='''

URL_MOJI_LOGIN = 'https://api.mojidict.com/parse/login'
URL_MOJI_SEARCH_V3 = 'https://api.mojidict.com/parse/functions/search_v3'
URL_MOJI_FETCH_WORDS = 'https://api.mojidict.com/parse/functions/nlt-fetchManyLatestWords'
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
def moji_fetch_word(word_id: str) -> dict:
    result = utils.request_post(URL_MOJI_FETCH_WORDS, json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "itemsJson": [{"objectId": word_id}],
        "skipAccessories": False
    }).json().get('result').get('result')[0]
    word = result.get('word')
    tts_url = moji_tts_url(word_id, 102)
    spell = word.get('spell')
    pron = word.get('pron', '') + word.get('accent', '')

    parts_of_speech = {}
    trans = {}
    for detail in result['details']:
        parts_of_speech[detail['objectId']] = detail['title'].replace('#', '・')
    for subdetail in result['subdetails']:
        trans[subdetail['objectId']] = {
            'title': f"[{parts_of_speech[subdetail['detailsId']]}]{subdetail['title']}" if subdetail[
                                                                                               'detailsId'] in parts_of_speech else
            subdetail['title'],
            'examples': []
        }
    for example in result['examples']:
        if example['subdetailsId'] in trans:
            trans[example['subdetailsId']]['examples'].append(
                (example['notationTitle'], example.get('trans') or ''))
    examples_html = ''
    for trans_id in trans.keys():
        t = trans[trans_id]
        examples_html += f'<div class="word-trans" onclick="changeDisplay(`{trans_id}`)">{t["title"]}</div><div id="trans-{trans_id}">'
        for e in t['examples']:
            examples_html += f'<div class="example-title">{e[0]}</div>'
            examples_html += f'<div class="example-trans">{e[1]}</div>'
        examples_html += '</div>'
    return {
        'id': word_id,
        'type': 102,
        'spell': spell,
        'pron': pron,
        'voice': f'[sound:{tts_url}]',
        'part_of_speech': " ".join(parts_of_speech.values()),
        'link': moji_get_link(word_id, 102),
        'examples': examples_html
    }


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


def moji_get_link(tar_id, tar_type):
    if tar_type == 102:
        return "https://www.mojidict.com/details/" + tar_id
    elif tar_type == 103:
        return "https://www.mojidict.com/example/" + tar_id
    elif tar_type == 120:
        return "https://www.mojidict.com/sentence/" + tar_id
    else:
        return ''


'''====================================================词典列表===================================================='''

dict_list = [
    {
        'name': 'baidu-v1',
        'able': True,
        'title': '百度翻译',
        'lang': ['all'],  # 'zh':中文, 'en': 英文, 'ja': 日文, 'all': 任意
        'icon': 'baidu-trans-logo.png',
        'audio-icon': 'audio-blue.svg',
        'template': 'baidu-panel.html',
        'func': baidu_trans,  # 函数参数为(text, from_lang), 即原文和原文语种, 返回为dict类型
        'style-file': 'baidu-panel.css',
    },
    {
        'name': 'moji-search',
        'able': True,
        'title': 'Moji辞書',
        'lang': ['zh', 'ja'],
        'icon': 'moji-dict-logo.png',
        'audio-icon': 'moji-voice.webp',
        'template': 'moji-panel.html',
        'func': moji_search,
        'style-file': 'moji-panel.css'
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
            template = d.get('template')
            func = d.get('func')
            style_file = d.get('style-file', None)
            dictionary = Dict(name, able, on, title, lang, icon, audio_icon, template, func, style_file)
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
                 template: str, func=None, style_file: str = None):
        self.name = name
        self.able = able
        self.on = on
        self.title = title
        self.lang = lang
        self.icon = icon
        self.audio_icon = audio_icon
        self.template = template
        self.func = func
        self.style_file = style_file

    @classmethod
    def message_result(cls, text: str = ''):
        return {'message': text}

    def do_trans(self, text, from_lang) -> dict:
        if not self.able or self.func is None:
            return self.message_result('该词典暂不可用')
        if from_lang not in self.lang and 'all' not in self.lang:
            return self.message_result('该词典不支持该语言')

        return self.func(text, from_lang)


# 用于获取所有词典和已开启词典列表
dicts = Dicts()
