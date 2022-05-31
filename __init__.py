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
__authors__ = 'mparati'

iconPath = os.path.dirname(__file__) + '/icon.png'
vscodeRecentsPath = Path.home() / '.config' / 'Code' / 'User' / 'globalStorage' / 'storage.json'


def getVscodeRecents():
    try:
        storage = json.load(open(vscodeRecentsPath, 'r'))
        items = storage['lastKnownMenubarData']['menus']['File']['items']
    except:
        return [], []

    for item in items:
        if item['id'] == 'submenuitem.35':
            items_filtred = item

    recents = items_filtred['submenu']['items']

    folders = []
    files = []
    for recent in recents:
        if recent['id'] == 'openRecentFolder':
            folders.append(recent['uri']['path'])
        elif recent['id'] == 'openRecentFile':
            files.append(recent['uri']['path'])

    return folders, files


def resizePath(path, maxchars=50):
    if len(path) <= maxchars:
        return path

    parts = path.split('/')
    parts.reverse()

    relativeLen = 0
    shortPath = ''

    for part in parts:
        if len(part) == 0: continue
        if len('.../' + part + '/' + shortPath) <= maxchars:
            shortPath = '/' + part + shortPath
            relativeLen += len(part)
        else:
            break

    return '...' + shortPath


def startWithSpace(string):
    return len(string) > 0 and not string.isspace() and string[0] != ' '


def makeRecentItem(path, recentType):
    return makeItem(
        resizePath(path),
        f'Open {recentType}',
        [TermAction('Open in Visual Studio Code', f'code "{path}"')]
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
        return makeItem('Visual Studio Code not installed')

    string = query.string

    if startWithSpace(string):
        return None

    string = string.strip().lower()
    folders, files = getVscodeRecents()

    if not folders and not files:
        return makeItem('Recents Files and Folders not found')

    items = []

    for el in folders + files:
        if not string in el.lower():
            continue

        elems = el.split('/')
        el = '/'.join(elems[:-1]) + '/' + f'<b>{elems[-1]}</b>'
        items.append(makeRecentItem(el, 'folder' if el in folders else 'file'))

    return items
