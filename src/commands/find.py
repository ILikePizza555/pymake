from .command import command
from enum import Enum, unique, auto
from typing import List, Dict, Tuple, Any, NamedTuple, Union
from io import IOBase
from itertools import takewhile
from getopt import getopt
from pathlib import Path

class SymlinkBehavior(Enum):
    NEVER_FOLLOW = "P",
    ALWAYS_FOLLOW = "L",
    WHEN_PROCESSING = "H"


def determine_behavior(options: List[str]) -> SymlinkBehavior:
    rv = None
    for o in options:
        try:
            rv = SymlinkBehavior(o)
        except ValueError:
            continue
    
    # Default behavior is to never follow symbolic links. 
    if rv is None:
        return SymlinkBehavior.NEVER_FOLLOW
    else:
        return rv

@unique
class OperandTokens(Enum):
    OPERAND_NAME = auto()
    OPERAND_VALUE = auto()
    LPAREN = auto()
    RPAREN = auto()
    NOT = auto()
    AND = auto()
    OR = auto()


def tokenize_operands(operand_strings: List[str]) -> List[Tuple[OperandTokens, str]]:
    rv = []

    while operand_strings:
        s = operand_strings.pop(0)

        if s == "(":
            rv.append((OperandTokens.LPAREN, s))
        elif s == ")":
            rv.append((OperandTokens.RPAREN, s))
        elif s == "!":
            rv.append((OperandTokens.NOT, s))
        elif s == "-a":
            rv.append((OperandTokens.AND, s))
        elif s == "-o":
            rv.append((OperandTokens.OR, s))
        elif s.startswith("-"):
            rv.append((OperandTokens.OPERAND_NAME, s[1:]))
        else:
            rv.append((OperandTokens.OPERAND_VALUE, s))
    
    return rv

def peek_token(tokens: List[Tuple[OperandTokens, str]], i: int = 0) -> OperandTokens:
    """
    Returns the type of the ith token in the list.
    """
    return tokens[i][0]

# Maps operand names to functions that consume a path and return a Boolean
PATH_OPERAND_EVALUATORS = {}

def operand(name: str):
    def wrapper(func):
        if name in PATH_OPERAND_EVALUATORS:
            raise ValueError(f"{name} already defined as an operand!")
        
        PATH_OPERAND_EVALUATORS[name] = func

        return func
    return wrapper

class Expression(NamedTuple):
    """
    Represents an operand expression (an operand and an optional number of values)
    """
    name: str
    values: List[str]

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        name = tokens.pop(0)[1]
        values = []

        while tokens and tokens[0][0] == OperandTokens.OPERAND_VALUE:
            values.append(tokens.pop(0)[1])
        
        return cls(name, values)

class BinaryOp(NamedTuple):
    left_expr: Expression
    op: str
    right_expr: Expression
    
def descend(path: Path) -> List[Path]:
    """
    Decends the given path. Returns a list of Paths to all files.
    """
    rv = []

    path_stack = list(path.iterdir()) if path.is_dir() else [path]
    i = 0

    # A while loop is used here instead of a for loop so we can iterate over the "stack" while adding items to it
    while i < len(path_stack):
        current_item: Path = path_stack[i]

        if current_item.is_dir():
            path_stack.extend(current_item.iterdir())
        else:
            #TODO: Add operand evaluation here
            rv.append(current_item)
        
        i += 1
    
    return rv

@command("find")
def find(args: List[str], env: Dict[str, str], f_in: IOBase, f_out: IOBase) -> int:
    opt: Tuple[List[Tuple[str, str]], List[str]] = getopt(args, "HLPv")

    # Flatten the options into a list of strings
    options: List[str] = [i[0][1:] for i in opt[0]]
    
    # Set variables to control program behavior
    behavior = determine_behavior(options)
    verbose = "v" in options

    file_paths = descend(Path(opt[1][0]))

    for f in file_paths:
        print(f, file=f_out)