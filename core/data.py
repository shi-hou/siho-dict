from dataclasses import dataclass


class Word:
    def __init__(self, text, lang, trans, voice_file):
        self.text = text
        self.lang = lang
        self.trans = trans
        self.voice_file = voice_file

