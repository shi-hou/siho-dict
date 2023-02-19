from core import utils
from core.setting import setting


class Anki:
    @classmethod
    def invoke(cls, action, **params):
        url = f"http://{setting.get('anki-address', '127.0.0.1')}:{setting.get('anki-port', '8765')}"
        key = setting.get('anki-key', None)
        response = utils.request_post(url, json={
            'action': action,
            'params': params,
            'key': key,
            'version': 6
        }).json()
        if len(response) != 2:
            raise Exception('response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('response is missing required error field')
        if 'result' not in response:
            raise Exception('response is missing required result field')
        if response['error'] is not None:
            raise Exception(response['error'])
        return response['result']

    @classmethod
    def create_deck_if_not_exists(cls, deckName: str) -> int:
        return cls.invoke('createDeck', deck=deckName)

    @classmethod
    def is_model_existing(cls, modelName: str):
        return modelName in cls.invoke('modelNames')

    @classmethod
    def create_model(cls, modelName: str, fields: list, css: str, templates: list):
        return cls.invoke("createModel", modelName=modelName, inOrderFields=fields, css=css, isCloze=False,
                          cardTemplates=templates)

    @classmethod
    def can_add_note(cls, deckName: str, modelName: str, fields: dict):
        notes = [{
            'deckName': deckName,
            'modelName': modelName,
            'fields': fields
        }]
        return cls.invoke("canAddNotes", notes=notes)[0]

    @classmethod
    def add_note(cls, deckName: str, modelName: str, fields: dict, audio: list = None):
        return cls.invoke("addNote", note={
            'deckName': deckName,
            'modelName': modelName,
            'fields': fields,
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
                "duplicateScopeOptions": {
                    "deckName": deckName,
                    "checkChildren": False,
                    "checkAllModels": False
                }
            },
            "audio": audio
        })

    @classmethod
    def find_notes(cls, **query):
        return cls.invoke("findNotes", query=' '.join([f'{key}:{value}' for key, value in query.items()]))

    @classmethod
    def store_media_file(cls, filename: str, path: str):
        return cls.invoke("storeMediaFile", filename=filename, path=path)

    @classmethod
    def is_media_file_existing(cls, filename: str):
        return filename in cls.invoke("getMediaFilesNames", pattern=filename)

    @classmethod
    def sync(cls):
        cls.invoke("sync")
