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

from UTIL import Agent,tofiles,DBs,database

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
    tofiles(messages[-1]["content"], dbs.workspace)
    return messages


def clarify(ai: Agent, dbs: DBs) -> List[dict]:
    messages = [ai.parsemsg("system",dbs.preprompts["qa"])]
    userinput = getprompt(dbs)
    while True:
        messages = ai.next(messages, userinput, step_name=currentfn())

        if messages[-1]["content"].strip() == "Nothing more to clarify.":
            breaks

        userinput = input('(answer in text, or "c" to move on)\n')

        if not userinput or userinput == "c":
            print("(LLM makes its own assumptions)")

            messages = ai.next(
                messages,
                "Make your own assumptions and state them explicitly before starting",
                step_name=currentfn(),
            )
            print()
            return messages

        userinput += (
            "\n\n"
            "Is anything else unclear? If yes, only answer in the form:\n"
            "{remaining unclear areas} remaining questions.\n"
            "{Next question}\n"
            'If everything is sufficiently clear, only answer "Nothing more to clarify.".'
        )

    return messages


def genspec(ai: Agent, dbs: DBs) -> List[dict]:
    messages = [
        ai.parsemsg("system",setup_sysmsg(dbs)),
        ai.parsemsg("system",f"Instructions: {dbs.input['prompt']}"),
    ]

    messages = ai.next(messages, dbs.preprompts["spec"], step_name=currentfn())

    dbs.memory["specification"] = messages[-1]["content"]

    return messages


def respec(ai: Agent, dbs: DBs) -> List[dict]:
    messages = json.loads(dbs.logs[genspec.__name__])
    messages += [ai.parsemsg("system",dbs.preprompts["respec"])]

    messages = ai.next(messages, step_name=currentfn())
    messages = ai.next(
        messages,
        (
            "Based on the conversation so far, please reiterate the specification for "
            "the program. "
            "If there are things that can be improved, please incorporate the "
            "improvements. "
            "If you are satisfied with the specification, just write out the "
            "specification word by word again."
        ),
        step_name=currentfn(),
    )

    dbs.memory["specification"] = messages[-1]["content"]
    return messages

def gen_clearcode(ai: Agent, dbs: DBs) -> List[dict]:
    messages = json.loads(dbs.logs[clarify.__name__])

    messages = [
        ai.parsemsg("system",setup_sysprompt(dbs)),
    ] + messages[1:]
    messages = ai.next(messages, dbs.preprompts["use_qa"], step_name=currentfn())

    tofiles(messages[-1]["content"], dbs.workspace)
    return messages

def gen_code(ai: Agent, dbs: DBs) -> List[dict]:
    messages = [
        ai.parsemsg("system",setup_sysprompt(dbs)),
        ai.parsemsg("user",f"Instructions: {dbs.input['prompt']}"),
        ai.parsemsg("user",f"Specification:\n\n{dbs.memory['specification']}"),
    ]
    messages = ai.next(messages, dbs.preprompts["use_qa"], step_name=currentfn())
    tofiles(messages[-1]["content"], dbs.workspace)
    return messages

def gen_entrypoint(ai: Agent, dbs: DBs) -> List[dict]:
    messages = ai.start(
        system=(
            "You will get information about a codebase that is currently on disk in "
            "the current folder.\n"
            "From this you will answer with code blocks that includes all the necessary "
            "unix terminal commands to "
            "a) install dependencies "
            "b) run all necessary parts of the codebase (in parallel if necessary).\n"
            "Do not install globally. Do not use sudo.\n"
            "Do not explain the code, just give the commands.\n"
            "Do not use placeholders, use example values (like . for a folder argument) "
            "if necessary.\n"
        ),
        user="Information about the codebase:\n\n" + dbs.workspace["output.txt"],
        step_name=currentfn(),
    )
    regex = r"```\S*\n(.+?)```"
    matches = re.finditer(regex, messages[-1]["content"], re.DOTALL)
    dbs.workspace["run.sh"] = "\n".join(match.group(1) for match in matches)
    return messages


CHECKS=[clarify,gen_clearcode,gen_entrypoint]

###################################################################################################################################


###################################################################################################################################

