from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Dict, List

import re

import datetime
from slugify import slugify
import json
import shutil

from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy as dcopy

import langchain
from langchain.schema import  AIMessage, HumanMessage, SystemMessage  ,ChatMessage
from langchain.chat_models import ChatGooglePalm



######################################################################################

PALM_API="AIzaSyAIzDH7NVopxUvOL8PAqBnKZqdmAoXeS28"

#################################################################################

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
    for msg in js:
        messages.append(wrapper[msg['role']](content=msg['content']))
    return messages


##################################################################################


def extractmessage(messages):
    return messages[-1].content

def getjson(specify):
    ss=specify.split('```')
    for s in ss:
        if s.find('json')==0:
            return s
    return None

def getassm(msg):
    m=msg.split('.')
    t=''
    for s in m:
        if s.find('?')==-1:
            t +=s
    return t


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


def parser(chat,team):
    specify=team.specify
    nms=[]
    itr=iter(json.loads(specify['result'][5:-1]).keys())
    while True:
        try:
            n=next(itr)
            nms.append(n)
        except:
            break
    print(nms)
    summ=chat#[len(chat.split("```")[0]):]
    #print(summ)
    #print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    files=[]
    for n in nms:
        try:
            #print((f'>>>>"FILENAME": \"{n}\"'))
            #temp=summ.find('"FILENAME": "tictactoe.py"')#.split('"CODE":')[1].split('"LANG":')[0]
            #print(f"########{temp}")
            file=summ[summ.find(f'"FILENAME": \"{n}\"'):].split('"CODE":')[1].split('"LANG":')[0]
            files.append((n,file))
        except:
            pass

    readme=chat.split("```")[0]
    files.append(("README.md", readme+"\n"+specify['result']))
    
    return files
    


def savetofiles(team,chat):
    
    #files=parsechat(chat)
    files=parser(chat,team)
    added=[]
    for name,file in files:
        temp=slugify(name)
        if temp in added:
            temp='2_'+temp
        else:
            pass
        added.append(temp)
        open(f'codes/{temp}',"w",encoding='utf-8').write(file)

def savelogs(team):
    
    data=['clarify','assume','specify']
    
    open("logs/clarify",'w',encoding='utf-8').write(json.dumps(team.clarify))
    #clarify=json.loads(open("log/clarify",'r',encoding='utf-8').read()) #to load
    
    open("logs/assume",'w',encoding='utf-8').write(json.dumps(team.assume))
    
    open("logs/specify",'w',encoding='utf-8').write(json.dumps(team.specify))
    
    
    

##################################################################################



class MyAgent:
    def __init__(self,dbm,temperature=0.1):
        self.temperature=temperature
        self.chatter=ChatGooglePalm(google_api_key=PALM_API,temperature=temperature,stream=True)
        self.label=dbm
        self.preprompt=self.setpreprompt()#choice of dbm decides : dbm=["clarification","specification","creation"]
    
    def setpreprompt(self):
        temp=open(f"preprompts/{self.label}",'r').read()
        return temp

    def parsemessage(self,choice,msg):
        wrapper={"system":SystemMessage , "user":HumanMessage , "assistant": AIMessage}
        return wrapper[choice](content=msg)
        
    def start(self,agentprompt,stepname=None):
        messages= [HumanMessage(content=self.preprompt+ agentprompt)]
        return self.next(messages,stepname=stepname)
    
    def next(self,messages: List[Dict[str, str]],prompt=None, *, stepname=None):
        if prompt:
            messages += [HumanMessage(content=prompt)]        
        response = self.chatter(messages)
        
        messages += [dcopy(response)]
        return messages
    

##################################################################################
class AgentTeam:
    def __init__(self,task):
        self.prompt=task
        self.clarify={"prompt":'',"result":''}
        self.assume={"prompt":'',"result":''}
        self.specify={"prompt":'',"result":''}
    
    
    def run(self):
        print(f"!!!!{self.prompt}")
        self.clarification()
        print(f">>>>{self.clarify['result']}")
        self.assumption()
        print(f"%%%%{self.assume['result']}")
        self.specification()
        print(f"$$$${self.specify['result']}")
        cod=self.creation()
        print("<><><><><><><><><><><><><><><>")
        return cod
        
    
    def clarification(self):#Create clarification
        cl=MyAgent("clarification")
        self.clarify['prompt'] = cl.preprompt+ self.prompt 
        
        self.clarify['result']= extractmessage(cl.start(self.prompt))
    
    def assumption(self):#create assumptions
        ass=MyAgent("assumption")
        tempas=input("Answer to some clarifications....")
        tempas='\nASSUMPTIONS: '+tempas
        assprompt=ass.preprompt+'\n INSTRUCTION : '+self.prompt+'\n CLARIFICATION: '+self.clarify['result']+tempas
        assume=ass.next([ass.parsemessage("user",assprompt)])
        
        self.assume['prompt'] = assprompt
        self.assume['result'] = tempas+'\n'+getassm(extractmessage(assume))
        
    def specification(self):#create specifications and return json object
        sp=MyAgent("specification")

        speprompt=sp.preprompt+'\n INSTRUCTION : '+self.prompt+'\n ASSUMPTIONS : '+self.assume['result']
        specify=sp.next([sp.parsemessage("user",speprompt)])      
        
        self.specify['prompt']=speprompt
        self.specify['result']=getjson(extractmessage(specify))
    
    def creation(self):
        create=MyAgent("creation")
        cprompt=create.preprompt+'\n SPECIFICATION : '+self.specify['result']
        messages=[create.parsemessage("user",self.prompt),create.parsemessage("assistant",self.assume['result']),create.parsemessage("user",cprompt)]
        cod=create.next(messages)
        
        return cod

        