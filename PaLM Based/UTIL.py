from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Dict, List

import re

import datetime
from slugify import slugify
import shutil

from pathlib import Path
from typing import Any, Dict, Optional

import langchain
from langchain.schema import  AIMessage, HumanMessage, SystemMessage  ,ChatMessage
from langchain.chat_models import ChatGooglePalm
PALM_API=""

logger = logging.getLogger(__name__)


def tojsonparser(messages):
    js=[]
    for msg in messages:
        role=''
        if type(msg)==langchain.schema.messages.SystemMessage:
            role='system'
        elif type(msg)==langchain.schema.messages.HumanMessage:
            role='user'
        else:
            role='assistant'
        js.append({"role":role,"content":msg.content})
    return js

def fromjsonparser(js):
    messages=[]
    wrapper={"system":SystemMessage , "user":HumanMessage , "assistant":AIMessage}
    #print(js[0])
    for msg in js:
        #print(f"$$$$${msg}")
        messages.append(wrapper[msg['role']](content=msg['content']))
    return messages
##################################################################################

class Agent:
    def __init__(self, temperature=0.1):
        self.temperature = temperature
        self.chatter = ChatGooglePalm(google_api_key=PALM_API,temperature=temperature,stream=True)

    def start(self, system, user, step_name):
        messages = [HumanMessage(content=system+'\n'+user)]
        return self.next(messages, step_name=step_name)

    def parsemsg(self,choice,msg):#choice=["system","user","assistant"]
        wrapper={"system":SystemMessage , "user":HumanMessage , "assistant": AIMessage}
        return wrapper[choice](content=msg)

    def next(self, messages: List[Dict[str, str]], prompt=None, *, step_name=None):
        if prompt:
            messages += [HumanMessage(content=prompt)]

        logger.debug(f"Start a new chat: {messages}")
        ##########
        response = self.chatter(messages)
        #########
        messages += [response]
        logger.debug(f"Chat finished: {messages}")

        return messages

#####################################################################################


def parsechat(chat):  
    regex = r"(\S+)\n\s*```[^\n]*\n(.+?)```"
    matches = re.finditer(regex, chat, re.DOTALL)
    #print(f"&&&&&{chat}")
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
        print(f"@@@@@@@@@{slugify(file_name)}")
        workspace[slugify(file_name)] = file_content

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
