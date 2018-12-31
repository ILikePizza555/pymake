from .command import command
from typing import List, Dict, Tuple
from io import IOBase
from itertools import takewhile
import enum

class LinkBehavior(enum.Enum):
    NEVER = 1,
    PROCESSING_ONLY = 2,
    ALWAYS = 3


def parse_flags(args: List[str]) -> Tuple[LinkBehavior, bool]:
    rv_behavior = None
    rv_verbose = False

    while args[0].startswith('-'):
        item = args.pop(0)

        if item == "-H":
            rv_behavior = LinkBehavior.PROCESSING_ONLY
        elif item == "-L":
            rv_behavior = LinkBehavior.ALWAYS
        elif item == "-v":
            rv_verbose = True
        else:
            raise ValueError(f"Unknown flag: {item}")
    
    return (rv_behavior, rv_verbose)

def parse_operands(args: List[str]):
    pass

@command("find")
def find(args: List[str], env: Dict[str, str], f_in: IOBase, f_out: IOBase) -> int:
    behavior, verbose = parse_flags(args)
    paths = list(takewhile(lambda s: not s.startswith("-") || s != "!" || s != "(", args))
    operands = parse_operands([len(paths):])