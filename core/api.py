import json

from core import utils

URL_LANG_DETECT = 'https://fanyi.baidu.com/langdetect'
URL_TRANS = 'https://fanyi.baidu.com/transapi'
URL_VOICE = 'https://fanyi.baidu.com/gettts'

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


def baidu_trans(text, from_lang) -> dict:
    # 非中文->中文, 中文(也可能是日文)->英文
    if from_lang == 'ja':
        from_lang = 'jp'
    to_lang = 'zh' if from_lang != 'zh' else 'en'
    resp = utils.request_post(URL_TRANS, data={
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


def moji_trans(text, from_lang) -> dict:
    if from_lang == 'zh':
        flang = 'zh-CN'
        tlang = 'ja'
    elif from_lang == 'ja':
        flang = 'ja'
        tlang = 'zh-CN'
    else:
        raise Exception('moji翻译不支持该语言')
    trans_dst = 'test~~~~~~~~~~~~~~~~~~~(测试数据，暂不发请求)'
    return {
        'type': 2,
        'text': text,
        'trans': trans_dst
    }


dict_list = [
    {
        'name': 'baidu-v1',
        'able': True,
        'title': '百度翻译',
        'lang': ['zh', 'en', 'ja'],
        'icon': 'baidu-trans-logo.png',
        'color': 'blue',
        'func': baidu_trans,
    },
    {
        'name': 'moji-search',
        'able': False,
        'title': 'Moji辞書',
        'lang': ['zh', 'en', 'ja'],
        'icon': 'moji-dict-logo.png',
        'color': 'red',
        'func': None,
    },
    {
        'name': 'moji-trans',
        'able': True,
        'title': 'Moji翻译',
        'lang': ['zh', 'ja'],
        'icon': 'moji-dict-logo.png',
        'color': 'red',
        'func': moji_trans,
    },
    {
        'name': 'bing',
        'able': False,
        'title': '必应词典',
        'lang': [],
        'icon': 'bing-dict-logo.png',
        'color': 'orange',
        'func': None,
    },
]


class Dict:
    def __init__(self, name: str, able: bool, on: bool, title: str, lang: list, icon: str, color: str, func):
        self.name = name
        self.able = able
        self.on = on
        self.title = title
        self.lang = lang
        self.icon = icon
        self.color = color
        self.func = func

    def do_trans(self, text, from_lang) -> dict:
        if not self.able or self.func is None:
            raise Exception('暂不支持该词典')

        return self.func(text, from_lang)


class DictServer:

    def __init__(self):
        self.dicts = []
        self.on_dicts = []
        self.dict_settings = utils.get_config().get('dict', {dict_list[0]['name']: {'on': True}})
        self.resetDict()

    def do_trans(self, text: str, from_lang: str) -> list:
        result = []
        for d in self.on_dicts:
            if from_lang in d.lang:
                result.append(d.do_trans(text, from_lang))
            else:
                result.append(None)
        return result

    def resetDict(self):
        self.dicts = []
        self.on_dicts = []
        for d in dict_list:
            name = d.get('name')
            able = d.get('able', False)
            on = able and self.dict_settings.get(name, {}).get("on", False)
            title = d.get('title')
            lang = d.get('lang')
            icon = d.get('icon')
            color = d.get('color')
            func = d.get('func')
            dictionary = Dict(name, able, on, title, lang, icon, color, func)
            self.dicts.append(dictionary)
            if on:
                self.on_dicts.append(dictionary)

    def setOn(self, index: int, on: bool):
        dict_name = self.dicts[index].name
        one_dict_setting = self.dict_settings.get(dict_name, {})
        one_dict_setting['on'] = on
        self.dict_settings[dict_name] = one_dict_setting
        utils.update_config({'dict': self.dict_settings})
        self.resetDict()


dict_server = DictServer()
