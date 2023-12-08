from typing import Callable, List, TypeVar,Optional


import inspect
import json
import os
import re
import subprocess
import random
import tempfile

from enum import Enum
from termcolor import colored

from UTIL import Agent,tofiles,DBs,database,fromjsonparser,tojsonparser

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dataclasses_json import dataclass_json



Step = TypeVar("Step", bound=Callable[[Agent, DBs], List[dict]])



#########################################################################################################




def colored(*args):
    return args[0]

def setup_sysprompt(dbs: DBs) -> str:
    return (
        dbs.preprompts["generate"] + "\nUseful to know:\n" + dbs.preprompts["philosophy"]
    )


def getprompt(dbs: DBs) -> str:
    assert (
        "prompt" in dbs.input or "main_prompt" in dbs.input
    ), "Please put your prompt in the file `prompt` in the project directory"

    if "prompt" not in dbs.input:
        print(
            colored("Please put the prompt in the file `prompt`, not `main_prompt", "red")
        )
        print()
        return dbs.input["main_prompt"]

    return dbs.input["prompt"]


def currentfn() -> str:
    return inspect.stack()[1].function

def simplegen(ai: Agent, dbs: DBs) -> List[dict]:
    messages = ai.start(setup_sysprompt(dbs), getprompt(dbs), step_name=currentfn())
    tofiles(messages[-1].content, dbs.workspace)
    return messages


def clarify(ai: Agent, dbs: DBs) -> List[dict]:
    
    userinput = getprompt(dbs)
    messages =[]

    while True:
        messages = ai.next(messages, dbs.preprompts["qa"]+"\n QUERY :"+userinput,step_name=currentfn())

        if messages[-1].content.strip() == "Nothing more to clarify.":
            break

        userinput = input('(answer in text, or "c" to move on)\n')

        if not userinput or userinput == "c":
            print("(LLM makes its own assumptions)")

            messages = ai.next(
                messages,
                "Make your own assumptions and state them explicitly before starting",
                step_name=currentfn(),
            )
            #print(messages)
            return messages

        userinput += (
            "\n\n"
            "Is anything else unclear? If yes, only answer in the form:\n"
            "{remaining unclear areas} remaining questions.\n"
            "{Next question}\n"
            'If everything is sufficiently clear, only answer "Nothing more to clarify.".'
        )
    #print(f"%%%%%%{messages}")
    return messages


def genspec(ai: Agent, dbs: DBs) -> List[dict]:
    messages = [
        ai.parsemsg("system",setup_sysmsg(dbs)),
        ai.parsemsg("system",f"Instructions: {dbs.input['prompt']}"),
    ]

    messages = ai.next(messages, dbs.preprompts["spec"], step_name=currentfn())

    dbs.memory["specification"] = messages[-1].content
    #print(f">>>>>{messages}")
    return messages


def gen_clearcode(ai: Agent, dbs: DBs) -> List[dict]:
    #print(f"******{fromjsonparser(dbs.logs[clarify.__name__])}")
    messages = fromjsonparser(json.loads(dbs.logs[clarify.__name__]))

   # messages = [
   #     ai.parsemsg("system",setup_sysprompt(dbs)),
   # ] + messages[1:]
    messages = ai.next(messages, setup_sysprompt(dbs)+"\n"+dbs.preprompts["use_qa"], step_name=currentfn())

    tofiles(messages[-1].content, dbs.workspace)
    return messages

def gen_code(ai: Agent, dbs: DBs) -> List[dict]:
    messages = [
        ai.parsemsg("system",setup_sysprompt(dbs)),
        ai.parsemsg("user",f"Instructions: {dbs.input['prompt']}"),
        ai.parsemsg("user",f"Specification:\n\n{dbs.memory['specification']}"),
    ]
    messages = ai.next(messages, dbs.preprompts["use_qa"], step_name=currentfn())
    tofiles(messages[-1].content, dbs.workspace)
    return messages


CHECKS=[clarify,gen_clearcode]

###################################################################################################################################


###################################################################################################################################

