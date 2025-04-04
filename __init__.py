# -*- coding: utf-8 -*-
"""
v0.5
  - convert to API 0.5
  - temporary removed rich html support due https://github.com/albertlauncher/albert/issues/1164
v0.6
  - convert to API 2.1
v0.7
  - convert to API 3.0
  - make albert-vscode open a new window instead of opening the last workspace
"""

import json
from pathlib import Path
from shutil import which
from typing import List, Literal, Optional, Tuple
from albert import *


md_name = "Visual Studio Code"
md_iid = "3.0"
md_description = "Open & search recent Visual Studio Code files and folders."
md_version = "0.7"
md_authors = ["@mparati31", "@bierchermuesli", "@noah-boeckmann"]
md_url = "https://github.com/mparati31/albert-vscode"
md_license = "unknown license"


class Plugin(PluginInstance, GlobalQueryHandler):
    ICON = [f"file:{Path(__file__).parent}/icon.png"]
    VSCODE_RECENT_PATH = Path.home() / ".config" / "Code" / "User" / "globalStorage" / "storage.json"
    EXECUTABLE = which("code")

    def __init__(self):
        GlobalQueryHandler.__init__(self)
        PluginInstance.__init__(self)

    # Tells albert the default trigger, may be changed by user
    def defaultTrigger(self):
        return 'vs '

    # Returns the following tuple: (recent files paths, recent folders paths).
    def get_visual_studio_code_recent(
        self,
    ) -> Tuple[List[str], List[str]]:
        storage = json.load(open(self.VSCODE_RECENT_PATH, "r"))
        menu_items = storage["lastKnownMenubarData"]["menus"]["File"]["items"]
        file_menu_items = list(filter(lambda item: item["id"] == "submenuitem.MenubarRecentMenu", menu_items))
        submenu_recent_items = file_menu_items[0]["submenu"]["items"]
        files = list(filter(lambda item: item["id"] == "openRecentFile", submenu_recent_items))
        folders = list(filter(lambda item: item["id"] == "openRecentFolder", submenu_recent_items))
        extract_path = lambda item: item["uri"]["path"]
        files_paths = list(map(extract_path, files))
        folders_paths = list(map(extract_path, folders))
        return files_paths, folders_paths

    # Returns the abbreviation of `path` that has `maxchars` character size.
    def resize_path(self, path: str | Path, maxchars: int = 45) -> str:
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
    def make_item(self, text: str, subtext: str = "", actions: List[Action] = []) -> StandardItem:
        return StandardItem(id=self.id(), iconUrls=self.ICON, text=text, subtext=subtext, actions=actions)

    # Return an item that create a new window.
    def make_new_window_item(self) -> StandardItem:
        return self.make_item(
            "New Empty Window", "Open new Visual Studio Code empty window", [Action(id=self.id(), text="Open in Visual Studio Code", callable=lambda: runDetachedProcess(cmdln=[self.EXECUTABLE, "-n"]))]
        )

    # Return a recent item.
    def make_recent_item(self, path: str | Path, recent_type: Literal["file", "folder"]) -> Item:
        resized_path = self.resize_path(path)
        path_splits = resized_path.split("/")
        working_dir_path, filename = path_splits[:-1], path_splits[-1]
        formatted_path = "{}/{}".format("/".join(working_dir_path), filename)

        return self.make_item(
            formatted_path, "Open Recent {}".format(recent_type), [Action(id=path, text="Open in Visual Studio Code", callable=lambda: runDetachedProcess(cmdln=[self.EXECUTABLE, path]))]
        )

    def handleTriggerQuery(self, query) -> Optional[List[Item]]:
        if not self.EXECUTABLE:
            return query.add(self.make_item("Visual Studio Code not installed"))

        query_text = query.string

        debug("query: '{}'".format(query_text))

        query_text = query_text.strip().lower()
        files, folders = self.get_visual_studio_code_recent()

        debug("vs recent files: {}".format(files))
        debug("vs recent folders: {}".format(folders))

        if not folders and not files:
            return [query.add(self.make_new_window_item()), query.add(self.make_item("Recent Files and Folders not found"))]

        items = []
        for element_name in ["New Empty Window"] + folders + files:
            if query_text not in element_name.lower():
                continue
            if element_name == "New Empty Window":
                item = query.add(self.make_new_window_item())
            else:
                item = query.add(self.make_recent_item(element_name, "folder" if element_name in folders else "file"))
            items.append(item)

        return items

    # avoid warning about calling a pure virtual function
    def handleGlobalQuery(self, query):
        return []
