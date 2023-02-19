# -*- coding: utf-8 -*-
"""
v0.5
  - convert to API 0.5
  - temporary removed rich html support due https://github.com/albertlauncher/albert/issues/1164
"""

import json
import os
from pathlib import Path
from shutil import which
from typing import List, Literal, Optional, Tuple
from albert import *


md_name = "Visual Studio Code"
md_iid = "0.5"
md_description = "Open & search recent Visual Studio Code files and folders."
md_id = "vs"
md_version = "0.5"
md_maintainers = ['@mparati31','@bierchermüesli']
md_url = "https://github.com/mparati31/albert-vscode"


ICON_PATH = os.path.dirname(__file__) + "/icon.png"
VSCODE_RECENT_PATH = Path.home() / ".config" / "Code" / "User" / "globalStorage" \
                     / "storage.json"
EXECUTABLE = which("code")


class Plugin(QueryHandler):
    def id(self):
        return md_id

    def name(self):
        return md_name

    def description(self):
        return md_description

    # Returns the following tuple: (recent files paths, recent folders paths).
    def get_visual_studio_code_recent(self,) -> Tuple[List[str], List[str]]:
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
    def resize_path(self,path: str | Path, maxchars: int = 45) -> str:
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

    # Return a item.
    def make_item(self,
            text: str,
            subtext: str = "",
            actions: List[Action] = []
    ) -> Item:
        return (Item(
            id=md_id,
            icon=[ICON_PATH],
            text=text,
            subtext=subtext,
            actions=actions
        ))

    # Return an item that create a new window.
    def make_new_window_item(self) -> Item:
        return self.make_item(
            "New Empty Window",
            "Open new Visual Studio Code empty window",
            [Action(id=md_id,text="Open in Visual Studio Code",
            callable=lambda: runDetachedProcess(cmdln=[EXECUTABLE]))]
        )

    # Return a recent item.
    def make_recent_item(self,
            path: str | Path,
            recent_type: Literal["file", "folder"]
    ) -> Item:
        resized_path = self.resize_path(path)
        path_splits = resized_path.split("/")
        working_dir_path, filename = path_splits[:-1], path_splits[-1]
        formatted_path = "{}/{}".format("/".join(working_dir_path), filename)

        return self.make_item(
            formatted_path,
            "Open Recent {}".format(recent_type),
            [Action(id=path,text="Open in Visual Studio Code",
            callable=lambda: runDetachedProcess(cmdln=[EXECUTABLE,path]))]
        )

    def handleQuery(self,query: Query) -> Optional[List[Item]]:

        if not EXECUTABLE:
            return query.add(self.make_item("Visual Studio Code not installed"))

        query_text = query.string

        debug("query: '{}'".format(query_text))


        query_text = query_text.strip().lower()
        files, folders = self.get_visual_studio_code_recent()

        debug("vs recent files: {}".format(files))
        debug("vs recent folders: {}".format(folders))

        if not folders and not files:
            return [
                query.add(self.make_new_window_item()),
                query.add(self.make_item("Recent Files and Folders not found"))
            ]

        items = []
        for element_name in ["New Empty Window"] + folders + files:
            if query_text not in element_name.lower():
                continue
            if element_name == "New Empty Window":
                item = query.add(self.make_new_window_item())
            else:
                item = query.add(self.make_recent_item(element_name,
                                        "folder" if element_name in folders else "file"))
            items.append(item)

        return items
