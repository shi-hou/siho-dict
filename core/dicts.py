import json
import os

import requests
from retry import retry
from sihodictapi import *

from core import utils
from core.anki import Anki
from core.languages import ALL_LANG, Lang

'''====================================================有道词典===================================================='''


# <editor-fold desc="有道词典">

def youdao_search(q: str, _):
    resp_json = Youdao.dict_search(q)
    result_body = {}
    fanyi = resp_json.get('fanyi')
    if fanyi:  # 输入为句子, 机器翻译
        result_body['trans_html'] = fanyi.get('tran').replace('\n', '<br>')
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
'''====================================================谷歌翻译===================================================='''


# <editor-fold desc="谷歌翻译">

def google_trans(text, _) -> dict:
    trans_text = Google.translate(text)
    return {'trans': trans_text.replace('\n', '<br>')}


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


'''====================================================福昕翻译===================================================='''


# <editor-fold desc="福昕翻译">

def foxit_translate(text: str, _) -> dict:
    resp = Foxit.translate(text)
    result = resp.get('result')
    return {'trans': result.replace('\n', '<br>')}


# </editor-fold>


'''====================================================金山词霸翻译===================================================='''


# <editor-fold desc="金山词霸翻译">

def iciba_translate(text: str, _) -> dict:
    resp = Iciba.translate(text)
    out = resp.get('content').get('out')
    return {'trans': out.replace('\n', '<br>')}


# </editor-fold>


'''====================================================沪江小D翻译===================================================='''


# <editor-fold desc="沪江小D翻译">

def hjenglish_translate(text: str, from_lang: Lang) -> dict:
    if from_lang is Lang.ZH:
        from_lang = Hujiang.Lang.CN
    elif from_lang is Lang.JA:
        from_lang = Hujiang.Lang.JP

    resp = Hujiang.translate(text, from_lang, Hujiang.Lang.CN)
    content = resp.get('data').get('content')
    return {'trans': content.replace('\r\n', '<br>')}


# </editor-fold>


'''====================================================沪江小D查词-日语===================================================='''


# <editor-fold desc="沪江小D查词-日语">

def hjenglish_dict_search_jp(text: str, _) -> dict:
    results = Hujiang.dict_search_jp(text).get('results')
    type = 'jc'
    if not results:
        results = Hujiang.dict_search_jp(text, 'cj').get('results')
        type = 'cj'
    if not results:
        return {}
    button_html_list = []
    word_html_list = []
    for index, result in enumerate(results):
        word_text = result.get('word_text')
        word_info = result.get('word_info')
        spell = word_info.get('spell')
        if spell:
            spell = f'[{spell}]'
        # audio = word_info.get('audio')    # TODO
        accent = word_info.get('accent', '')
        button_html_list.append(f'<a class="select-button" onclick="select_word({index})">'
                                f'<span class="button-word">{word_text}</span>'
                                f'<span class="button-spell">{spell}</span>'
                                f'</a>')
        simple_html = ''
        for simple in result.get('simple'):
            title = simple.get('title')
            if title:
                title = f'【{title}】'
            paraphrases = simple.get('paraphrases')
            if type == 'jc':
                simple_paraphrases_html = f'<ol><li>{"</li><li>".join(paraphrases)}</li></ol>'
            else:
                simple_paraphrases_html = f'{"；".join(paraphrases)}'
            simple_html += f'<div class="simple-title">{title}</div>' \
                           f'<div class="simple-definition">{simple_paraphrases_html}</div>'
        detail_html_list = []
        for detail in result.get('details'):
            category = detail.get('category')
            paraphrases_html = ''
            for paraphrase in detail.get('paraphrases'):
                paraphrase_ja = paraphrase.get('paraphrase_ja')
                paraphrase_zh = paraphrase.get('paraphrase_zh')
                examples_html = ''
                for example in paraphrase.get('examples'):
                    examples_html += f'<div class="example">{example.get("example", "")}</div>' \
                                     f'<div class="trans">{example.get("trans", "")}</div>'
                paraphrases_html += '<li>' \
                                    f'<div class="paraphrase-ja">{paraphrase_ja}</div>' \
                                    f'<div class="paraphrase-zh">{paraphrase_zh}</div>' \
                                    f'<div class="examples">{examples_html}</div>' \
                                    '</li>'
            detail_html = '<div class="detail">' \
                          f'<div class="category">{category}</div>' \
                          f'<div class="paraphrases"><ol>{paraphrases_html}</ol></div>' \
                          '</div>'
            detail_html_list.append(detail_html)
        details_html = '\n'.join(detail_html_list)
        word_html = '<div class="word">' \
                    '<div class="word-header">' \
                    '<div class="word-info">' \
                    f'<div class="word-text">{word_text}</div>' \
                    f'<div class="pronounces">{spell}<span class="accent">{accent}</span></div>' \
                    '</div>' \
                    '' \
                    f'<div class="sample">{simple_html}</div>' \
                    '</div>' \
                    f'<div class="word-details">{details_html}</div>' \
                    '</div>'
        word_html_list.append(word_html)
    return {
        'buttons-html': '\n'.join(button_html_list),
        'words-html': '\n'.join(word_html_list)
    }


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
            'url': moji_tts_url(target_id, target_type)
        },
        'link': Moji.data_url(target_id, target_type),
        'part_of_speech': " ".join(parts_of_speech.values()),
        'trans': trans_html,
        'examples': examples_html
    }


@retry(tries=3)
def moji_fetch_word(word_id: str) -> dict:
    return Moji.fetch_words(word_id).get('result').get('result')[0]


@retry(tries=3)
def moji_tts_url(target_id, target_type) -> str:
    return Moji.tts_fetch(target_id, target_type).get('result').get('result').get('url')


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
        'support-lang': [Lang.ZH, Lang.EN],  # 支持翻译的语言, 见core.languages.Lang枚举, 默认为Lang的所有枚举值
        'icon': 'youdao-logo.png',
        'audio-icon': 'youdao-voice.png',
        'template': 'youdao-panel.html',
        'func': youdao_search,  # 翻译, 参数为(text, from_lang), 即原文和原文语种, 返回为dict类型
        'style-file': 'youdao-panel.css',
        'anki-add-note': youdao_add_anki_note,  # 将单词添加到Anki, 接收查词结果, 返回添加结果信息字符串
        'anki-create-deck-and-model': youdao_create_deck_and_model_if_not_exists  # 创建Anki牌组和模板, 返回牌组名和模板名
    },
    {
        'name': 'google-trans',
        'able': True,
        'title': '谷歌翻译',
        'icon': 'google_translate_logo.webp',
        'template': 'common-trans-panel.html',
        'style-file': 'common-trans-panel.css',
        'func': google_trans,
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
        'name': 'foxit-trans',
        'able': True,
        'title': '福昕翻译',
        'icon': 'foxit_logo.png',
        'template': 'common-trans-panel.html',
        'style-file': 'common-trans-panel.css',
        'func': foxit_translate,
    },
    {
        'name': 'iciba-trans',
        'able': True,
        'title': '金山词霸翻译',
        'icon': 'iciba-logo.png',
        'template': 'common-trans-panel.html',
        'style-file': 'common-trans-panel.css',
        'func': iciba_translate,
    },
    {
        'name': 'hjenglish-trans',
        'able': True,
        'title': '沪江小D翻译',
        'icon': 'hjenglish_logo.webp',
        'template': 'common-trans-panel.html',
        'style-file': 'common-trans-panel.css',
        'func': hjenglish_translate,
    },
    {
        'name': 'hjenglish-dict-jp',
        'able': True,
        'title': '沪江小D日语词典',
        'support-lang': [Lang.ZH, Lang.JA],
        'icon': 'hjenglish_logo.webp',
        'template': 'hjenglish-panel.html',
        'style-file': 'hjenglish-dict-panel.css',
        'func': hjenglish_dict_search_jp,
    },
    {
        'name': 'moji',
        'able': True,
        'title': 'Moji辞書',
        'support-lang': [Lang.ZH, Lang.JA],
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
            support_lang = d.get('support-lang', ALL_LANG)  # 默认支持所有语言
            icon = d.get('icon')
            audio_icon = d.get('audio-icon')
            template = d.get('template')
            func = d.get('func')
            style_file = d.get('style-file', None)
            anki_add_note_func = d.get('anki-add-note', None)
            anki_create_deck_and_model_func = d.get('anki-create-deck-and-model', None)
            dictionary = Dict(name, able, on, title, support_lang, icon, audio_icon, template, func, style_file,
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
    def __init__(self, name: str, able: bool, on: bool, title: str, support_lang: list, icon: str,
                 audio_icon: str = None, template: str = None, func=None, style_file: str = None,
                 anki_add_note_func=None, anki_create_deck_and_model=None):
        self.name = name
        self.able = able
        self.on = on
        self.title = title
        self.support_lang = support_lang
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
        if from_lang not in self.support_lang:
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
