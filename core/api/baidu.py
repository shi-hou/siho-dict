import json

from core.utils import dict_get, post

URL_LANG_DETECT = 'https://fanyi.baidu.com/langdetect'
URL_TRANS = 'https://fanyi.baidu.com/transapi'
URL_VOICE = 'https://fanyi.baidu.com/gettts'


def lang_detect(text):
    lan = post(URL_LANG_DETECT, data={'query': text}).json()['lan']
    if lan != 'en':
        lan = 'jp'
    return lan


def trans(text):
    resp = post(URL_TRANS, data={
        'from': lang_detect(text),
        'to': 'zh',
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    if resp_type == 1:
        trans_result = ''
        result = json.loads(resp['result'])
        # print(result)
        voice = dict_get(result, 'voice')
        if voice is not None:
            trans_result += f"英{voice[0]['en_phonic']}\t"
            trans_result += f"美{voice[1]['us_phonic']}\n"
        mean = result['content'][0]['mean']
        for m in mean:
            trans_result += f"{dict_get(m, 'pre', '')}\n"
            for cont in m['cont']:
                trans_result += f"{cont};"
            trans_result += "\n"
        return trans_result
    elif resp_type == 2:
        return resp['data'][0]['dst']
    else:
        raise Exception('what?! type!!!!')


def get_voice(text, lan='en'):
    return post(URL_VOICE, data={
        'lan': lan,
        'text': text,
        'spd': 3,
        'source': 'web'
    }).json()
