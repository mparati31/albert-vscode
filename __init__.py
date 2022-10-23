# -*- coding: utf-8 -*-

"""Opens recent Visual Studio Code files and folders.

Synopsis: <trigger> <filter>"""

import json
import os
from distutils.log import debug
from pathlib import Path
from shutil import which
from typing import List, Literal, Optional, Tuple

from albert import *

__title__ = "Visual Studio Code"
__version__ = "0.4.3"
__triggers__ = ["vs"]
__autors__ = "Manuel Parati"

ICON_PATH = os.path.dirname(__file__) + "/icon.png"
VSCODE_RECENT_PATH = Path.home() / ".config" / "Code" / "User" / "globalStorage" \
                     / "storage.json"
EXECUTABLE = which("code")


# Returns the following tuple: (recent files paths, recent folders paths).
def get_visual_studio_code_recent() -> Tuple[List[str], List[str]]:
    storage = json.load(open(VSCODE_RECENT_PATH, "r"))
    menu_items = storage["lastKnownMenubarData"]["menus"]["File"]["items"]
    file_menu_items = list(filter(
        lambda item: item["id"] == "submenuitem.MenubarRecentMenu", menu_items))
    submenu_recent_items = file_menu_items[0]["submenu"]["items"]
    files = list(filter(
        lambda item: item["id"] == "openRecentFile", submenu_recent_items))
    folders = list(filter(
        lambda item: item["id"] == "openRecentFolder", submenu_recent_items))
    extract_path = lambda item: item["uri"]["path"]
    files_paths = list(map(extract_path, files))
    folders_paths = list(map(extract_path, folders))
    return files_paths, folders_paths


# Returns the abbreviation of `path` that has `maxchars` character size.
def resize_path(path: str | Path, maxchars: int = 45) -> str:
    filepath = Path(path)
    if len(str(filepath)) <= maxchars:
        return str(filepath)
    else:
        parts = filepath.parts
        # If the path is contains only the pathname, then it is returned as is.
        if len(parts) == 1:
            return str(filepath)
        relative_len = 0
        short_path = ""
        # Iterates on the reverse path elements and adds them until the relative
        # path exceeds `maxchars`.
        for part in reversed(parts):
            if len(part) == 0:
                continue
            if len(".../{}/{}".format(part, short_path)) <= maxchars:
                short_path = "/{}{}".format(part, short_path)
                relative_len += len(part)
            else:
                break
        return "...{}".format(short_path)


# Return True if string start with space.
def start_with_space(string: str) -> bool:
    return len(string) > 0 and not string.isspace() and string[0] != " "


# Return a item.
def make_item(
        text: str,
        subtext: str = "",
        actions: List[ProcAction] = []
) -> Item:
    return Item(
        id=__title__,
        icon=ICON_PATH,
        text=text,
        subtext=subtext,
        actions=actions
    )


# Return an item that create a new window.
def make_new_window_item() -> Item:
    return make_item(
        "New Empty Window",
        "Open new Visual Studio Code empty window",
        [ProcAction("Open in Visual Studio Code", [EXECUTABLE], "-n")]
    )


# Return a recent item.
def make_recent_item(
        path: str | Path,
        text_underline: str,
        recent_type: Literal["file", "folder"]
) -> Item:
    resized_path = resize_path(path)
    path_splits = resized_path.split("/")
    working_dir_path, filename = path_splits[:-1], path_splits[-1]
    formatted_path = "{}/<b>{}</b>".format("/".join(working_dir_path), filename)
    if text_underline != "" and not text_underline.isspace():
        if text_underline in formatted_path:
            formatted_path = formatted_path.replace(text_underline,
                                                    "<u>{}</u>".format(text_underline))
        else:
            formatted_path = formatted_path.replace("...", "<u>...</u>")
    return make_item(
        formatted_path,
        "Open Recent <b>{}</b>".format(recent_type),
        [ProcAction("Open in Visual Studio Code", [EXECUTABLE, path])]
    )


def handleQuery(query: Query) -> Optional[List[Item]]:
    if not query.isTriggered:
        return None

    if not EXECUTABLE:
        return make_item("Visual Studio Code not installed")

    query_text = query.string

    debug("query: '{}'".format(query_text))

    if start_with_space(query_text):
        return None

    query_text = query_text.strip().lower()
    files, folders = get_visual_studio_code_recent()

    debug("files: {}".format(files))
    debug("folders: {}".format(folders))

    if not folders and not files:
        return [
            make_new_window_item(),
            make_item("Recent Files and Folders not found")
        ]

    items = []
    for element_name in folders + files + ["New Empty Window"]:
        if query_text not in element_name.lower():
            continue
        if element_name == "New Empty Window":
            item = make_new_window_item()
        else:
            item = make_recent_item(element_name, query_text,
                                    "folder" if element_name in folders else "file")

        items.append(item)

    return items
