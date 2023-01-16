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


def baidu_lang_detect(text):
    return utils.request_post(URL_LANG_DETECT, data={'query': text}).json()['lan']


def baidu_trans(text):
    from_lang = baidu_lang_detect(text)
    to_lang = 'zh' if from_lang != 'zh' else 'en'
    print(text,': ', from_lang, '->', to_lang)
    resp = utils.request_post(URL_TRANS, data={
        'from': baidu_lang_detect(text),
        'to': to_lang,
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    result_body = None
    if resp_type == 1:
        result_body = {'type': 1, 'text': text}
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None and from_lang == 'en':
            result_body['voice'] = [{
                'pron': f"英{voice[0]['en_phonic']}",
                'url': f'https://fanyi.baidu.com/gettts?lan=uk&text={text}&spd=3&source=web'
            }, {
                'pron': f"美{voice[1]['us_phonic']}",
                'url': f'https://fanyi.baidu.com/gettts?lan=en&text={text}&spd=3&source=web'
            }]
        mean = result['content'][0]['mean']
        result_body['pre'] = []
        for m in mean:
            result_body['pre'].append({
                'title': m.get('pre', ''),
                'trans': m.get('cont')
            })

    elif resp_type == 2:
        result_body = {
            'type': 2,
            'text': text,
            'trans': resp['data'][0]['dst']
        }
    return result_body


def baidu_get_voice(text, lan):
    return utils.request_post(URL_VOICE, data={
        'lan': lan,
        'text': text,
        'spd': 3,
        'source': 'web'
    }).content


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
