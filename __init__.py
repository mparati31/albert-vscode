# -*- coding: utf-8 -*-

"""Open Visual Studio Code recents file and folders.

Synopsis: <trigger> <filter>"""

import os
import json

from albert import *
from pathlib import Path
from shutil import which

__title__ = 'Visual Studio Code'
__version__ = '0.4.3'
__triggers__ = ['vs']
__authors__ = 'mparati31'

iconPath = os.path.dirname(__file__) + '/icon.png'
vscodeRecentsPath = Path.home() / '.config' / 'Code' / 'User' / 'globalStorage' / 'storage.json'


def getVscodeRecents():
    try:
        storage = json.load(open(vscodeRecentsPath, 'r'))
        items = storage['lastKnownMenubarData']['menus']['File']['items']
    except:
        return [], []

    for item in items:
        if item['id'] == 'submenuitem.36':
            items_filtred = item

    recents = items_filtred['submenu']['items']

    folders = []
    files = []
    for recent in recents:
        if recent['id'] == 'openRecentFolder':
            folders.append(recent['uri']['path'])
        elif recent['id'] == 'openRecentFile':
            files.append(recent['uri']['path'])

    return files, folders


def resizePath(path, maxchars=50):
    if len(path) <= maxchars:
        return path

    parts = path.split('/')
    parts.reverse()

    relativeLen = 0
    shortPath = ''

    for part in parts:
        if len(part) == 0: continue
        if len('.../{}/{}'.format(part, shortPath)) <= maxchars:
            shortPath = '/{}{}'.format(part, shortPath)
            relativeLen += len(part)
        else:
            break

    return '...{}'.format(shortPath)


def startWithSpace(string):
    return len(string) > 0 and not string.isspace() and string[0] != ' '


def makeRecentItem(path, recentType):
    resizedPath = resizePath(path)
    pathSplits = resizedPath.split('/')
    formatted_path = '{}/<b>{}</b>'.format('/'.join(pathSplits[:-1]), pathSplits[-1])
    return makeItem(
        formatted_path,
        f'<i>Open Recent <b>{recentType}</b></i>',
        [TermAction('Open in Visual Studio Code', f'code "{path}"')]
    )


def makeNewWindowItem():
    return makeItem(
        '<b>New Empty Window</b>',
        'Open new Visual Studio Code empty window',
        [TermAction('Open in Visual Studio Code', 'code -n')]
    )


def makeItem(text, subtext='', actions=[]):
    return Item(
                id = __title__,
                icon = iconPath,
                text = text,
                subtext = subtext,
                actions = actions
            )


def handleQuery(query):
    if not query.isTriggered:
        return None

    if not which('code'):
        return makeItem('<b>Visual Studio Code not installed</b>')

    query_str = query.string

    if startWithSpace(query_str):
        return None

    query_str = query_str.strip().lower()
    files, folders = getVscodeRecents()

    if not folders and not files:
        return makeItem('<b>Recents Files and Folders not found</b>')

    items = []

    for element_name in folders + files + ['New Empty Window']:
        if not query_str in element_name.lower():
            continue

        if element_name == 'New Empty Window':
            item = makeNewWindowItem()
        else:
            item = makeRecentItem(element_name, 'Folder' if element_name in folders else 'File')

        items.append(item)

    return items
