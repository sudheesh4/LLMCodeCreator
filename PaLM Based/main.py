
import json
import logging

from pathlib import Path

from UTIL import Agent,database,DBs,tojsonparser
from UTIL2 import CHECKS

def main(
    project_path: str = "projects/example",
    temperature: float = 1.0,
):
    ai = Agent(
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
        dbs.logs[step.__name__] = json.dumps(tojsonparser(messages))



if __name__ == "__main__":
    main()
    