from enum import Enum


class Lang(str, Enum):
    ZH = 'zh'
    '''中文'''

    EN = 'en'
    '''英语'''

    JA = 'ja'
    '''日语'''


ALL_LANG = [lang for lang in Lang]
