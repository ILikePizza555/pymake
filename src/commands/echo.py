from .command import command
from typing import List, Dict
from io import IOBase

@command("echo")
def echo(args: List[str], env: Dict[str, str], f_in: IOBase, f_out: IOBase) -> int:
    print(*args, file=f_out)

    return 0