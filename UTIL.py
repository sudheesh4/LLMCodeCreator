from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Dict, List

import openai
import re

import datetime
import shutil

from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


openai.api_base = "http://localhost:1234/v1" 
openai.api_key = "" 

class Agent:
    def __init__(self,model, temperature=0.1):
        self.temperature = temperature
        self.model = model

    def start(self, system, user, step_name):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        return self.next(messages, step_name=step_name)

    def parsemsg(self,choice,msg):#choice=["system","user","assistant"]
        return {"role":choice,"content":msg}

    def next(self, messages: List[Dict[str, str]], prompt=None, *, step_name=None):
        if prompt:
            messages += [{"role": "user", "content": prompt}]

        logger.debug(f"Start a new chat: {messages}")
        ##########
        response = openai.ChatCompletion.create(
            messages=messages,
            stream=True,
            model=self.model,
            temperature=self.temperature,
        )
        #########
        chat = []
        for chunk in response:
            delta = chunk["choices"][0]["delta"]  # type: ignore
            msg = delta.get("content", "")
            print(msg, end="")
            chat.append(msg)
        messages += [{"role": "assistant", "content": "".join(chat)}]
        logger.debug(f"Chat finished: {messages}")

        return messages

#####################################################################################


def parsechat(chat):  
    regex = r"(\S+)\n\s*```[^\n]*\n(.+?)```"
    matches = re.finditer(regex, chat, re.DOTALL)

    files = []
    for match in matches:
        path = re.sub(r'[<>"|?*]', "", match.group(1))
        path = re.sub(r"^\[(.*)\]$", r"\1", path)
        path = re.sub(r"^`(.*)`$", r"\1", path)
        path = re.sub(r"\]$", "", path)

        code = match.group(2)

        files.append((path, code))

    readme = chat.split("```")[0]
    files.append(("README.md", readme))

    return files


def tofiles(chat, workspace):
    workspace["output.txt"] = chat

    files = parsechat(chat)
    for file_name, file_content in files:
        workspace[file_name] = file_content

###################################################################################################



class database:
    def __init__(self, path, in_memory_dict: Optional[Dict[Any, Any]] = None):
        self.path = Path(path).absolute()
        self.path.mkdir(parents=True, exist_ok=True)
        self.in_memory_dict = in_memory_dict

    def __contains__(self, key):
        return (self.path / key).is_file()

    def __getitem__(self, key):
        if self.in_memory_dict is not None:
            return self.in_memory_dict.__getitem__(str((self.path / key).absolute()))
        full_path = self.path / key
        if not full_path.is_file():
            raise KeyError(f"File '{key}' not found at '{self.path}'")
        with full_path.open("r", encoding="utf-8") as f:
            return f.read()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, val):
        if self.in_memory_dict is not None:
            return self.in_memory_dict.__setitem__(str((self.path / key).absolute()), val)
        full_path = self.path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(val, str):
            full_path.write_text(val, encoding="utf-8")
        else:
            raise TypeError("val must be either a str or bytes")

@dataclass
class DBs:
    memory: database
    logs: database
    preprompts: database
    input: database
    workspace: database





#####################################################################################################################