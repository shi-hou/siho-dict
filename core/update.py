from datetime import datetime

from core import utils

OWNER = 'shi-hou'
REPO = 'siho-dict'
TAG = 'v0.2.4'
GITHUB_URL = f'https://github.com/{OWNER}/{REPO}'


def check_for_update():
    try:
        latest = utils.request_get(f'https://api.github.com/repos/{OWNER}/{REPO}/releases/latest').json()
        current = utils.request_get(f'https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}').json()
        return {
            'success': True,
            'latest_tag': latest.get('tag_name'),
            'is_latest': str2date(latest.get('published_at')) == str2date(current.get('published_at')),
            'latest_download_url': latest.get('assets')[0].get('browser_download_url')
        }
    except:
        return {'success': False}


def str2date(date_str: str):
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
