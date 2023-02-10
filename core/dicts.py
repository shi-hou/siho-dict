import json
import os

import requests
from retry import retry
from sihodictapi import Youdao, Baidu, Iciba, Moji

from core import utils
from core.anki import Anki

'''====================================================有道词典===================================================='''


# <editor-fold desc="有道词典">

def youdao_search(q: str, _):
    resp_json = Youdao.dict_search(q)
    result_body = {}
    fanyi = resp_json.get('fanyi')
    if fanyi:  # 输入为句子, 机器翻译
        result_body['trans_html'] = fanyi.get('tran')
        return result_body

    ec = resp_json.get('ec')
    if ec:  # 输入英文单词
        result_body['exam_type'] = " | ".join(ec.get('exam_type', []))
        word = ec.get('word')
        if not word:
            return {}
        result_body['support-anki'] = True
        result_body['return-phrase'] = word.get('return-phrase')
        if word.get('ukphone'):
            result_body['ukphone'] = f"英/{word.get('ukphone', '')}/"
        if word.get('usphone'):
            result_body['usphone'] = f"美/{word.get('usphone', '')}/"
        speech_titles = ['speech', 'ukspeech', 'usspeech']
        for speech_title in speech_titles:
            speech = word.get(speech_title)
            if speech:
                result_body[speech_title] = {
                    'type': 'audio',
                    'filename': f'youdao_{speech_title}_{result_body["return-phrase"]}.mp3',
                    'url': f'https://dict.youdao.com/dictvoice?audio={speech}'
                }
        trs = word.get('trs')
        trans_html = ''
        for tr in trs:
            trans_html += f'''
                <div class="pos_and_tran">
                    <div class="pos">{tr.get('pos', '')}</div>
                    <div class="tran">{tr.get('tran', '')}</div>
                </div>
                '''
        result_body['trans_html'] = trans_html
        return result_body

    ce = resp_json.get('ce')
    if ce:  # 输入中文词语
        word = ce.get('word')
        result_body['return-phrase'] = word.get('return-phrase', '')
        trs = word.get('trs')
        trans_html = ''
        for tr in trs:
            trans_html += f'''
            <div class="text_and_tran">
                <div class="text">{tr.get('#text', '')}</div>
                <div class="tran">{tr.get('#tran', '')}</div>
            </div>
            '''
        result_body['trans_html'] = trans_html
        return result_body
    # 查无结果
    return {}


def youdao_add_anki_note(data: dict) -> str:
    deck_name, model_name = youdao_create_deck_and_model_if_not_exists()

    fields = data.copy()
    speech_titles = ['speech', 'ukspeech', 'usspeech']
    for title in speech_titles:
        fields[title] = ''

    if not Anki.can_add_note(deck_name, model_name, fields):
        return '单词已存在, 无需重复添加'

    audio = []
    for title in speech_titles:
        speech = data.get(title)
        if speech:
            filename = speech.get('filename')
            path = utils.store_tmp_file(filename, speech.get('url'))
            audio.append({
                'path': path,
                'filename': filename,
                'fields': [title]
            })

    Anki.add_note(deck_name, model_name, fields, audio)
    return '添加成功'


def youdao_create_deck_and_model_if_not_exists() -> (str, str):
    config = utils.get_config()

    deck_name = config.get('anki-youdao-deck', 'Youdao')
    Anki.create_deck_if_not_exists(deck_name)

    model_name = config.get('anki-youdao-model', 'Youdao')
    if not Anki.is_model_existing(model_name):
        fields = ['return-phrase', 'speech', 'ukphone', 'ukspeech', 'usphone', 'usspeech', 'trans_html', 'exam_type']

        css = utils.read_asset_file('anki', 'youdao', 'youdao-style.css')
        front_template = utils.read_asset_file('anki', 'youdao', 'youdao-front.html')
        back_template = utils.read_asset_file('anki', 'youdao', 'youdao-back.html')
        card_templates = [{
            "Name": "单词",
            "Front": front_template,
            "Back": back_template
        }]
        Anki.create_model(model_name, fields, css, card_templates)
    return deck_name, model_name


# </editor-fold>


'''====================================================百度翻译===================================================='''


# <editor-fold desc="百度翻译">

def baidu_trans(text, _) -> dict:
    text = text.replace('\n', ' ').replace('\r', ' ')
    from_lang = Baidu.lang_detect(text).get('lan')
    resp = Baidu.translate(text, from_lang)
    resp_type = resp['type']
    result_body = {
        'from_lang': from_lang,
        'type': resp_type,
    }
    if resp_type == 1:
        result_body['text'] = text
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None and from_lang == 'en':
            result_body['support-anki'] = True
            if voice[0]['en_phonic']:
                result_body['pron_uk'] = f"英{voice[0]['en_phonic']}"
            if voice[1]['us_phonic']:
                result_body['pron_us'] = f"美{voice[1]['us_phonic']}"
        trans = ''
        for mean in result['content'][0]['mean']:
            trans += f'''<div class="pos">{mean.get('pre', '')}</div>'''
            trans += f'''<div class="trans">{';'.join(mean.get('cont'))}</div>'''
    else:  # elif resp_type == 2:
        trans = f'''<div>{resp['data'][0]['dst']}</div>'''
    result_body['trans'] = trans
    return result_body


# </editor-fold>


'''====================================================金山词霸翻译===================================================='''


# <editor-fold desc="金山词霸翻译">

def iciba_translate(text: str, _) -> dict:
    resp = Iciba.translate(text)
    out = resp.get('content').get('out')
    return {'out': out.replace('\n', '<br>').replace('\r', '<br>')}


# </editor-fold>


'''====================================================Moji辞書===================================================='''


# <editor-fold desc="Moji辞書">


def moji_search(text, _) -> dict:
    search_results = Moji.search_v3(text).get('result').get('searchResults')
    if len(search_results) == 0:
        return {}
    target_id = search_results[0].get('tarId')
    target_type = Moji.DataType.Word
    result = moji_fetch_word(target_id)
    word = result.get('word')

    parts_of_speech = {}
    trans = {}
    for detail in result['details']:
        parts_of_speech[detail['objectId']] = detail['title'].replace('#', '・')
    trans_html = '<ol>'
    for subdetail in result['subdetails']:
        trans_html += f'<li>{subdetail["title"]}</li>'
        if subdetail['detailsId'] in parts_of_speech:
            if parts_of_speech[subdetail['detailsId']]:
                trans_title = f"[{parts_of_speech[subdetail['detailsId']]}]{subdetail['title']}"
            else:
                trans_title = subdetail['title']
            trans[subdetail['objectId']] = {
                'title': trans_title,
                'examples': []
            }
    trans_html += '</ol>'
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
        'support-anki': True,
        'title': search_results[0].get('title'),
        'target_id': target_id,
        'target_type': str(target_type),
        'spell': word.get('spell'),
        'accent': word.get('accent', ''),
        'pron': word.get('pron', ''),
        'excerpt': word.get('excerpt', ''),
        'sound': {
            'type': 'audio',
            'filename': f'moji_{target_id}.mp3',
            'url': Moji.tts_fetch(target_id, target_type).get('result').get('result').get('url')
        },
        'link': Moji.data_url(target_id, target_type),
        'part_of_speech': " ".join(parts_of_speech.values()),
        'trans': trans_html,
        'examples': examples_html
    }


@retry(tries=3)
def moji_fetch_word(word_id: str) -> dict:
    return Moji.fetch_words(word_id).get('result').get('result')[0]


def moji_add_anki_note(data: dict) -> str:
    deck_name, model_name = moji_create_deck_and_model_if_not_exists()

    fields = data.copy()
    fields['sound'] = ''
    if not Anki.can_add_note(deck_name, model_name, fields):
        return '单词已存在, 无需重复添加'

    audio = []
    sound = data.get('sound')
    if sound:
        filename = sound.get('filename')
        path = utils.store_tmp_file(filename, sound.get('url'))
        audio.append({
            'path': path,
            'filename': filename,
            'fields': ['sound']
        })

    Anki.add_note(deck_name, model_name, fields, audio)
    return '添加成功'


def moji_create_deck_and_model_if_not_exists() -> (str, str):
    config = utils.get_config()

    deck_name = config.get('anki-moji-deck', 'Moji')
    Anki.create_deck_if_not_exists(deck_name)

    model_name = config.get('anki-moji-model', 'Moji')
    if not Anki.is_model_existing(model_name):
        fields = ['title', 'note', 'target_id', 'target_type', 'spell', 'accent', 'pron', 'excerpt', 'sound', 'link',
                  'part_of_speech', 'trans', 'examples']
        css = utils.read_asset_file('anki', 'moji', 'moji-style.css')
        front_template = utils.read_asset_file('anki', 'moji', 'moji-front.html')
        back_template = utils.read_asset_file('anki', 'moji', 'moji-back.html')
        card_templates = [{
            "Name": "MojiToAnki 3",
            "Front": front_template,
            "Back": back_template
        }]
        Anki.create_model(model_name, fields, css, card_templates)

    media_file_list = [name for name in os.listdir(utils.get_asset_path('anki', 'moji')) if name.startswith('_')]
    for media_file in media_file_list:
        if not Anki.is_media_file_existing(media_file):
            Anki.store_media_file(media_file, utils.get_asset_path('anki', 'moji', media_file))

    return deck_name, model_name


# </editor-fold>


'''====================================================词典列表===================================================='''

dict_list = [
    {
        'name': 'youdao',
        'able': True,
        'title': '有道词典',
        'exclude_lang': ['ja'],  # 不翻译的语言, 'zh':中文, 'en': 英文, 'ja': 日文
        'icon': 'youdao-logo.png',
        'audio-icon': 'youdao-voice.png',
        'template': 'youdao-panel.html',
        'func': youdao_search,  # 翻译, 参数为(text, from_lang), 即原文和原文语种, 返回为dict类型
        'style-file': 'youdao-panel.css',
        'anki-add-note': youdao_add_anki_note,  # 将单词添加到Anki, 接收查词结果, 返回添加结果信息字符串
        'anki-create-deck-and-model': youdao_create_deck_and_model_if_not_exists  # 创建Anki牌组和模板, 返回牌组名和模板名
    },
    {
        'name': 'baidu',
        'able': True,
        'title': '百度翻译',
        'icon': 'baidu-trans-logo.png',
        'template': 'baidu-panel.html',
        'func': baidu_trans,
        'style-file': 'baidu-panel.css',
    },
    {
        'name': 'iciba-trans',
        'able': True,
        'title': '金山词霸翻译',
        'icon': 'iciba-logo.png',
        'template': 'iciba-trans-panel.html',
        'style-file': 'iciba-panel.css',
        'func': iciba_translate,
    },
    {
        'name': 'moji',
        'able': True,
        'title': 'Moji辞書',
        'exclude_lang': ['en'],
        'icon': 'moji-dict-logo.png',
        'audio-icon': 'moji-voice.webp',
        'template': 'moji-panel.html',
        'func': moji_search,
        'style-file': 'moji-panel.css',
        'anki-add-note': moji_add_anki_note,
        'anki-create-deck-and-model': moji_create_deck_and_model_if_not_exists
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
            exclude_lang = d.get('exclude_lang', [])
            icon = d.get('icon')
            audio_icon = d.get('audio-icon')
            template = d.get('template')
            func = d.get('func')
            style_file = d.get('style-file', None)
            anki_add_note_func = d.get('anki-add-note', None)
            anki_create_deck_and_model_func = d.get('anki-create-deck-and-model', None)
            dictionary = Dict(name, able, on, title, exclude_lang, icon, audio_icon, template, func, style_file,
                              anki_add_note_func, anki_create_deck_and_model_func)
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
    def __init__(self, name: str, able: bool, on: bool, title: str, exclude_lang: list, icon: str,
                 audio_icon: str = None, template: str = None, func=None, style_file: str = None,
                 anki_add_note_func=None, anki_create_deck_and_model=None):
        self.name = name
        self.able = able
        self.on = on
        self.title = title
        self.exclude_lang = exclude_lang
        self.icon = icon
        self.audio_icon = audio_icon
        self.template = template
        self.func = func
        self.style_file = style_file
        self.anki_add_note_func = anki_add_note_func
        self.anki_create_deck_and_model_func = anki_create_deck_and_model

    @classmethod
    def message_result(cls, text: str = ''):
        return {'message': text}

    def do_trans(self, text, from_lang) -> dict:
        if not self.able or self.func is None:
            return self.message_result('该词典暂不可用')
        if from_lang in self.exclude_lang:
            return self.message_result('该词典不支持该语言')

        return self.func(text, from_lang)

    def is_anki_able(self):
        return self.anki_add_note_func and self.anki_create_deck_and_model_func

    def add_anki_note(self, data: dict) -> str:
        if not data.get('support-anki'):
            return '暂不支持将该单词添加到Anki'
        try:
            result_txt = self.anki_add_note_func(data)
            if utils.get_config().get('anki-auto-sync', False):
                Anki.sync()
            return result_txt
        except requests.exceptions.ConnectionError:
            return '无法连接AnkiConnect, 请确认Anki已启动并重试'
        except Exception as err:
            return str(err)


# 用于获取所有词典和已开启词典列表
dicts = Dicts()
