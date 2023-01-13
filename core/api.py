import json

from core import utils

URL_LANG_DETECT = 'https://fanyi.baidu.com/langdetect'
URL_TRANS = 'https://fanyi.baidu.com/transapi'
URL_VOICE = 'https://fanyi.baidu.com/gettts'


def baidu_lang_detect(text):
    lan = utils.post(URL_LANG_DETECT, data={'query': text}).json()['lan']
    if lan != 'en':
        lan = 'jp'
    return lan


def baidu_trans(text):
    resp = utils.post(URL_TRANS, data={
        'from': baidu_lang_detect(text),
        'to': 'zh',
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    if resp_type == 1:
        trans_result = ''
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None:
            trans_result += f"英{voice[0]['en_phonic']} "
            trans_result += f"美{voice[1]['us_phonic']}<br/>"
        mean = result['content'][0]['mean']
        for m in mean:
            trans_result += f"{m.get('pre', '')}<br/>"
            for cont in m['cont']:
                trans_result += f"{cont};"
            trans_result += "<br/>"
        return trans_result
    elif resp_type == 2:
        return resp['data'][0]['dst']
    else:
        raise Exception('what?! type!!!!')


def baidu_get_voice(text, lan='en'):
    return utils.post(URL_VOICE, data={
        'lan': lan,
        'text': text,
        'spd': 3,
        'source': 'web'
    }).json()


dict_list = [
    {
        'name': 'baidu-v1',
        'enable': True,
        'title': '百度翻译',
        'icon': 'baidu-trans-logo.png',
        'api': baidu_trans,
    },
    {
        'name': 'moji',
        'enable': False,
        'title': 'Moji辞書',
        'icon': 'moji-dict-logo.png',
        'api': None,
    },
    {
        'name': 'bing',
        'enable': False,
        'title': '必应词典',
        'icon': 'bing-dict-logo.png',
        'api': None,
    },
]
