
import openai
openai.api_base = "http://localhost:1234/v1" # point to the local server
openai.api_key = "" # no need for an API key

import json
import logging

from pathlib import Path

from UTIL import Agent,database,DBs
from UTIL2 import CHECKS

def main(
    project_path: str = "projects/example",
    model: str = "local-llm",
    temperature: float = 1.0,
):
    ai = Agent(
        model=model,
        temperature=temperature,
    )

    input_path = Path(project_path).absolute()
    memory_path = input_path / "memory"
    workspace_path = input_path / "workspace"

    dbs = DBs(
        memory=database(memory_path),
        logs=database(memory_path / "logs"),
        input=database(input_path),
        workspace=database(workspace_path),
        preprompts=database(Path(__file__).parent / "preprompts"),
    )

    for step in CHECKS:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = json.dumps(messages)



if __name__ == "__main__":
    main()
    