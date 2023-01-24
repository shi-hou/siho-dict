import hashlib
import json
from retry import retry

from core import utils
from core.anki import Anki

'''====================================================有道词典===================================================='''


# <editor-fold desc="有道词典">

def youdao_search(q: str, _):
    S = "web"
    k = "webdict"
    time = len(q + k) % 10
    x = "Mk6hqtUp33DGGtoS63tTJbMUYjRrG1Lu"
    r = q + k

    def y(t):
        m = hashlib.md5()
        m.update(t.encode('utf-8'))
        return m.hexdigest()

    resp = utils.request_post(url='https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4',
                              data={
                                  'q': q,
                                  'le': 'en',
                                  't': time,
                                  'client': S,
                                  'sign': y(S + q + str(time) + x + y(r)),
                                  'keyfrom': k
                              })
    resp_json = resp.json()
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
        result_body['return-phrase'] = word.get('return-phrase')
        if word.get('ukphone'):
            result_body['ukphone'] = f"英/{word.get('ukphone', '')}/"
        if word.get('usphone'):
            result_body['usphone'] = f"美/{word.get('usphone', '')}/"
        speech_titles = ['speech', 'usspeech', 'ukspeech']
        for speech_title in speech_titles:
            speech = word.get(speech_title)
            if speech:
                result_body[speech_title] = {
                    'type': 'audio',
                    'filename': f'youdao_{speech}.mp3',
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


# </editor-fold>


'''====================================================百度翻译===================================================='''


# <editor-fold desc="百度翻译">

def baidu_lang_detect(text):
    return utils.request_post('https://fanyi.baidu.com/langdetect', json={'query': text}).json()['lan']


# TODO 百度获取发音十有八九为空, b''
def baidu_trans(text, _) -> dict:
    from_lang = baidu_lang_detect(text)
    # 非中文->中文, 中文(也可能是日文)->英文
    to_lang = 'zh' if from_lang != 'zh' else 'en'
    resp = utils.request_post('https://fanyi.baidu.com/transapi', json={
        'from': from_lang,
        'to': to_lang,
        'query': text,
        'source': 'txt'
    }).json()
    resp_type = resp['type']
    result_body = {
        'from_lang': from_lang,
        'type': resp_type,
        'text': text
    }
    if resp_type == 1:
        result = json.loads(resp['result'])
        voice = result.get('voice')
        if voice is not None and from_lang == 'en':
            if voice[0]['en_phonic']:
                result_body['pron_uk'] = f"英{voice[0]['en_phonic']}"
                result_body['voice_uk'] = {
                    'type': 'audio',
                    'filename': f'baidu_uk_{text}.mp3',
                    'url': f'https://fanyi.baidu.com/gettts?lan=uk&text={text}&spd=3&source=web',
                }
            if voice[1]['us_phonic']:
                result_body['pron_us'] = f"美{voice[1]['us_phonic']}"
                result_body['voice_us'] = {
                    'type': 'audio',
                    'filename': f'baidu_us_{text}.mp3',
                    'url': f'https://fanyi.baidu.com/gettts?lan=en&text={text}&spd=3&source=web'
                }
        trans = ''
        for mean in result['content'][0]['mean']:
            trans += f'''<div class="pos">{mean.get('pre', '')}</div>'''
            trans += f'''<div class="trans">{';'.join(mean.get('cont'))}</div>'''
    else:  # elif resp_type == 2:
        trans = f'''<div>{resp['data'][0]['dst']}</div>'''
    result_body['trans'] = trans
    return result_body


def baidu_add_anki_note(data: dict) -> str:
    if data.get('from_lang') != 'en' or data.get('type') != 1:
        return '暂不支持将该单词添加到Anki'

    deck_name, model_name = baidu_create_deck_and_model_if_not_exists()

    fields = data.copy()
    fields['voice_uk'] = ''
    fields['voice_us'] = ''

    if not Anki.can_add_note(deck_name, model_name, fields):
        return '单词已存在, 无需重复添加'

    audio = []
    audio_titles = ['voice_uk', 'voice_us']
    for title in audio_titles:
        voice = data.get(title)
        if voice:
            filename = voice.get('filename')
            path = utils.store_tmp_file(filename, voice.get('url'))
            audio.append({
                'path': path,
                'filename': filename,
                'fields': [title]
            })

    Anki.add_note(deck_name, model_name, fields, audio)
    return '添加成功'


def baidu_create_deck_and_model_if_not_exists() -> (str, str):
    config = utils.get_config()

    deck_name = config.get('anki-baidu-deck', 'Baidu')
    Anki.create_deck_if_not_exists(deck_name)

    model_name = config.get('anki-baidu-model', 'Baidu')
    if not Anki.is_model_existing(model_name):
        fields = ['text', 'pron_uk', 'voice_uk', 'pron_us', 'voice_us', 'trans']
        css = '''
            .voice, .pos, .trans {
                font-family: Arial, Microsoft Yahei;
                font-size: 16px;
            }
            
            .text {
                font-weight: bold;
                font-family: Arial, Microsoft Yahei;
                font-size: 20px;
            }
            
            .pos {
                padding-top: 10px;
                color: #888683;
            }
        '''
        back_template = '''
                <div class="text">{{text}}</div>
                <div class="voice">{{pron_uk}}{{voice_uk}}</div>
                <div class="voice">{{pron_us}}{{voice_us}}</div>
                <div>{{trans}}</div>
                '''
        card_templates = [
            {
                "Name": "单词",
                "Front": '<div class="text">{{text}}</div>',
                "Back": back_template
            },
            {
                "Name": "发音",
                "Front": '''<div class="voice">{{pron_uk}}{{voice_uk}}</div>
                                <div class="voice">{{pron_us}}{{voice_us}}</div>''',
                "Back": back_template
            },
            {
                "Name": "中文",
                "Front": "<div>{{trans}}</div>",
                "Back": back_template
            }
        ]
        Anki.create_model(model_name, fields, css, card_templates)
    return deck_name, model_name


# </editor-fold>

'''====================================================Moji辞書===================================================='''

# <editor-fold desc="Moji辞書">


_ClientVersion = 'js2.12.0'
_ApplicationId = 'E62VyFVLMiW7kvbtVq3p'
_InstallationId = '7d959a18-48c4-243c-7486-632147466544'
g_os = 'PCWeb'
g_ver = 'v4.4.1.20221229'


@retry(tries=3)
def moji_login(email: str, password: str):
    return utils.request_post('https://api.mojidict.com/parse/login', json={
        "username": email,
        "password": password,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "_InstallationId": _InstallationId
    }).json().get('sessionToken')


def moji_search(text, _) -> dict:
    search_results = utils.request_post('https://api.mojidict.com/parse/functions/search_v3', json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "langEnv": "zh-CN_ja",
        "searchText": text
    }).json().get('result').get('searchResults')

    if len(search_results) == 0:
        return {}

    word_id = search_results[0].get('tarId')
    title = search_results[0].get('title')
    return moji_fetch_word(word_id, title)


@retry(tries=3)
def moji_fetch_word(word_id: str, title: str) -> dict:
    result = utils.request_post('https://api.mojidict.com/parse/functions/nlt-fetchManyLatestWords', json={
        "_InstallationId": _InstallationId,
        "_ClientVersion": _ClientVersion,
        "_ApplicationId": _ApplicationId,
        "itemsJson": [{"objectId": word_id}],
        "skipAccessories": False
    }).json().get('result').get('result')[0]
    word = result.get('word')
    tts_url = moji_tts_url(word_id, 102)
    spell = word.get('spell')
    accent = word.get('accent', '')
    pron = word.get('pron', '')
    excerpt = word.get('excerpt', '')

    parts_of_speech = {}
    trans = {}
    for detail in result['details']:
        parts_of_speech[detail['objectId']] = detail['title'].replace('#', '・')
    trans_html = '<ol>'
    for subdetail in result['subdetails']:
        trans_html += f'<li>{subdetail["title"]}</li>'
        trans[subdetail['objectId']] = {
            'title': f"[{parts_of_speech[subdetail['detailsId']]}]{subdetail['title']}" if subdetail[
                                                                                               'detailsId'] in parts_of_speech else
            subdetail['title'],
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
        'title': title,
        'target_id': word_id,
        'target_type': '102',
        'spell': spell,
        'accent': accent,
        'pron': pron,
        'excerpt': excerpt,
        'sound': {
            'type': 'audio',
            'filename': f'moji_{word_id}.mp3',
            'url': tts_url
        },
        'link': moji_get_link(word_id, 102),
        'part_of_speech': " ".join(parts_of_speech.values()),
        'trans': trans_html,
        'examples': examples_html
    }


@retry(tries=3)
def moji_tts_url(tarId: str, tarType: int):
    return utils.request_post('https://api.mojidict.com/parse/functions/tts-fetch', json={
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
        css = '''@font-face {
  font-family: HiraMinProN-W6;
  src: url("_HiraMinProN-W6.ttf");
}

.replay-button svg {
    width: 20px;
    height: 20px;
}

.replay-button svg path {
    fill: #FF5252;
}

.to-moji {
    text-decoration: none;
    display: inline-flex;
    vertical-align: middle;
    margin: 3px;
}

.to-moji svg {
    width: 20px;
    height: 20px;
}

.card {
    min-height: 100%;
    font-size: 14px;
    font-family: "Hiragino Kaku Gothic Pro",Meiryo,MS Gothic,Tahoma,Arial,PingFangSC-Regular,Microsoft Yahei,"黑体";
    text-align: left;
    color: black;
    background: #f8f8f8;
    display: block;
}

.card.nightMode  {
    color: #fafafc;
    background: #0e0e10;
}


.nightMode .spell, .nightMode .pron-and-accent {
    color: #fafafc;
}

.spell {
    color: #3d454c;
    font-size: 36px;
    font-weight: 600;
    font-family: HiraMinProN-W6,HiraMinProN;
}

.pron-and-accent {
    font-size: 16px;
    color: #3d454c;
    line-height: 1.4;
}

.path-of-speech {
    line-height: 3;
}

#sound {
    position:fixed;
    bottom:0;
    left:0;
}

#link {
    position:fixed;
    bottom:0;
    right:30px;
}

.front-trans {
    font-size: 16px;
}

.front-trans li {
    padding-bottom: 10px
}

.word-trans {
    font-size: 16px;
    background: #acacac1a;
    border-radius: 15px;
    padding: 10px;
    margin-bottom: 16px;
}

.nightMode .word-trans {
    background: #acacac1a
}

.example-title {
    padding-left: 16px;
    font-size: 16px;
    line-height: 20px; 
}

.example-trans {
    padding-left: 16px;
    color: #8b8787;
    font-size: 14px;
    line-height: 18px;
    margin-bottom: 24px;
}

.note {
    font-size:15px;
    color: #FF5252;
    border: 1px solid #FF5252;
    border-radius: 15px;
    padding: 10px;
}

.sound {
    float: right
}

ruby rt {
    font-weight: 400;
    font-size: 11px;
    text-align: center;
    font-family: "Hiragino Kaku Gothic Pro",Meiryo,MS Gothic,Tahoma,Arial,PingFangSC-Regular,Microsoft Yahei,"黑体";
}

            '''
        font_template = '<div class="spell">{{spell}}</div>'
        back_template = '''<div class="spell">{{spell}}</div>
<div class="pron-and-accent">{{pron}}{{accent}}</div>
<div class="path-of-speech">{{part_of_speech}}</div>
<div>
    <span class="sound">{{sound}}</span>
    <a class="to-moji" href="{{MojiToAnki_link:link}}">
        <svg t="1670999911770" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="25742" width="16" height="16"><path d="M817.078857 119.954286l-5.266286-4.827429a39.424 39.424 0 0 0-50.395428 2.779429l-24.576 22.893714-4.754286 5.339429-3.657143 5.851428a39.424 39.424 0 0 0 6.363429 44.470857l38.473143 41.252572-36.644572 0.146285-13.312 0.512a245.467429 245.467429 0 0 0-228.205714 244.809143V628.297143l0.438857 6.363428a39.424 39.424 0 0 0 38.912 32.987429h33.645714l6.363429-0.512a39.424 39.424 0 0 0 32.987429-38.838857V480.768l0.658285-10.752c6.509714-67.218286 63.341714-119.808 132.388572-119.808h162.889143l7.533714-0.658286a56.246857 56.246857 0 0 0 32.548571-93.842285L817.078857 119.954286z m-392.338286 5.851428a17.042286 17.042286 0 0 0-17.042285-17.042285H201.947429l-7.753143 0.219428A136.557714 136.557714 0 0 0 65.389714 245.248v577.536l0.219429 7.753143c4.022857 71.753143 63.488 128.731429 136.338286 128.731428h620.178285l7.68-0.146285a136.557714 136.557714 0 0 0 128.804572-136.338286V613.376a17.042286 17.042286 0 0 0-17.042286-17.042286h-68.242286a17.042286 17.042286 0 0 0-17.115428 17.042286v209.408l-0.219429 4.242286a34.157714 34.157714 0 0 1-33.865143 29.915428H201.874286l-4.242286-0.292571a34.157714 34.157714 0 0 1-29.842286-33.865143V245.248l0.292572-4.242286a34.157714 34.157714 0 0 1 33.865143-29.842285h205.750857a17.042286 17.042286 0 0 0 17.042285-17.115429V125.805714z" fill="#FF5252" p-id="25743"></path></svg>
    </a>
</div>
{{#note}}
<div class="note">{{note}}</div>
{{/note}}
<br/>
{{^examples}}
<div style="font-size: 16px;">{{trans}}{{^trans}}{{excerpt}}{{/trans}}</div>
{{/examples}}
<div>{{examples}}</div>
<script>
    var replayButton = document.getElementsByClassName('replay-button')[0];
    if(replayButton){
        replayButton.innerHTML='<svg t="1670944272402" class="playImage" viewBox="0 0 1137 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="9821" xmlns:xlink="http://www.w3.org/1999/xlink" width="17.765625" height="16"><path d="M798.776889 282.453333a358.513778 358.513778 0 0 1 0 482.816 45.397333 45.397333 0 0 1-19.683556 23.324445 46.193778 46.193778 0 1 1-63.374222-67.015111 269.539556 269.539556 0 0 0 13.312-382.122667 47.502222 47.502222 0 0 1-22.755555-33.621333 47.160889 47.160889 0 0 1 38.912-54.101334 46.421333 46.421333 0 0 1 30.094222 5.404445c10.808889 4.949333 19.285333 14.051556 23.495111 25.315555z m161.564444-168.504889a554.325333 554.325333 0 0 1 153.031111 382.805334c0 167.082667-73.955556 316.529778-190.577777 418.588444l-0.056889-0.113778a46.364444 46.364444 0 0 1-84.878222-26.282666c0-18.261333 10.524444-34.019556 25.827555-41.642667l-0.170667-0.227555a464.384 464.384 0 0 0 159.345778-350.321778 464.042667 464.042667 0 0 0-129.308444-321.649778 47.160889 47.160889 0 1 1 66.844444-61.155556zM464.042667 33.735111C529.408-27.534222 632.035556-2.275556 632.035556 102.684444v818.232889c0 103.936-101.432889 131.527111-168.106667 68.892445l-231.992889-237.340445H90.567111c-59.505778 0-90.225778-33.564444-90.225778-90.282666V361.415111c0-57.742222 29.752889-90.282667 90.225778-90.282667h141.425778L463.985778 33.735111z m77.824 840.931556V151.722667c0-71.111111-30.378667-31.971556-61.098667-1.877334-54.158222 52.963556-135.224889 139.207111-202.126222 211.569778H150.755556c-44.828444 0-60.188444 16.270222-60.188445 60.131556v180.508444c0 44.771556 14.449778 60.131556 60.188445 60.131556h126.407111c67.299556 71.964444 149.105778 158.321778 203.320889 211.797333 31.061333 30.72 61.326222 69.006222 61.326222 0.682667z" p-id="9822"></path></svg>';
    }
</script>
<script>
    function changeDisplay(transId) {
        const trans = document.getElementById('trans-' + transId);
        if (trans.style.display === 'none')
            trans.style.display = 'block'
        else
            trans.style.display = 'none'
    }
</script>

<script>
    rtList = document.getElementsByTagName('rt')
    for (let i = 0; i < rtList.length; i++) {
        rtList[i].innerText = rtList[i].getAttribute('hiragana')
    }
</script>

                '''
        card_templates = [{
            "Name": "AnkiToMoji v2.0.0",
            "Front": font_template,
            "Back": back_template
        }]
        Anki.create_model(model_name, fields, css, card_templates)

    if not Anki.is_media_file_existing('_HiraMinProN-W6.ttf'):
        Anki.store_media_file('_HiraMinProN-W6.ttf', utils.get_resources_path('fonts', 'HiraMinProN-W6.ttf'))

    return deck_name, model_name


# </editor-fold>

'''====================================================词典列表===================================================='''

dict_list = [
    {
        'name': 'youdao',
        'able': True,
        'title': '有道词典',
        'lang': ['en', 'zh'],
        'icon': 'youdao-logo.png',
        'audio-icon': 'youdao-voice.png',
        'template': 'youdao-panel.html',
        'func': youdao_search,
        'style-file': 'youdao-panel.css',
    },
    {
        'name': 'baidu-v1',
        'able': True,
        'title': '百度翻译',
        'lang': ['all'],  # 'zh':中文, 'en': 英文, 'ja': 日文, 'all': 任意
        'icon': 'baidu-trans-logo.png',
        'audio-icon': 'audio-blue.svg',
        'template': 'baidu-panel.html',
        'func': baidu_trans,  # 翻译, 参数为(text, from_lang), 即原文和原文语种, 返回为dict类型
        'style-file': 'baidu-panel.css',
        'anki-add-note': baidu_add_anki_note,  # 将单词添加到Anki, 接收查词结果, 返回添加结果信息字符串
        'anki-create-deck-and-model': baidu_create_deck_and_model_if_not_exists  # 创建Anki牌组和模板, 返回牌组名和模板名
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
            lang = d.get('lang')
            icon = d.get('icon')
            audio_icon = d.get('audio-icon')
            template = d.get('template')
            func = d.get('func')
            style_file = d.get('style-file', None)
            anki_add_note_func = d.get('anki-add-note', None)
            anki_create_deck_and_model_func = d.get('anki-create-deck-and-model', None)
            dictionary = Dict(name, able, on, title, lang, icon, audio_icon, template, func, style_file,
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
    def __init__(self, name: str, able: bool, on: bool, title: str, lang: list, icon: str, audio_icon: str,
                 template: str, func=None, style_file: str = None, anki_add_note_func=None,
                 anki_create_deck_and_model=None):
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
        self.anki_add_note_func = anki_add_note_func
        self.anki_create_deck_and_model_func = anki_create_deck_and_model

    @classmethod
    def message_result(cls, text: str = ''):
        return {'message': text}

    def do_trans(self, text, from_lang) -> dict:
        if not self.able or self.func is None:
            return self.message_result('该词典暂不可用')
        if from_lang not in self.lang and 'all' not in self.lang:
            return self.message_result('该词典不支持该语言')

        return self.func(text, from_lang)

    def is_anki_able(self):
        return self.anki_add_note_func and self.anki_create_deck_and_model_func


# 用于获取所有词典和已开启词典列表
dicts = Dicts()
