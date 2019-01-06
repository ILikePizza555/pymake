from .command import command, CommandParseError
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

    If tokens is empty, a ValueError is thrown.
    """
    if not tokens:
        raise ValueError("tokens is empty")

    return tokens[i][0]

def eat_token(tokens: List[Tuple[OperandTokens, str]], token: OperandTokens, i: int = 0) -> str:
    """
    Compares the ith token's type with the one provided. If they are equivalent, the value of the token is returned.
    Otherwise and exception is thrown.
    """
    if not tokens:
        raise CommandParseError("find", "", f"Expected token {token}")

    if peek_token(tokens, i) != token:
        raise CommandParseError("find", tokens[i][1], f"Expected token {token}")

    return tokens.pop(i)[1]
        

# Maps operand names to functions that consume a path and return a Boolean
PATH_OPERAND_EVALUATORS = {}

def operand(name: str):
    def wrapper(func):
        if name in PATH_OPERAND_EVALUATORS:
            raise ValueError(f"{name} already defined as an operand!")
        
        PATH_OPERAND_EVALUATORS[name] = func

        return func
    return wrapper

class ASTPrimary(NamedTuple):
    """
    Represents a primary expression (an operand and an optional number of values that evaluate to a boolean value)
    """
    name: str
    values: List[str]

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        """
        Consumes tokens from the list to form a primary. Assumes that the list of tokens starts with a valid primary.
        EBNF: `primary = NAME, {VALUE}`

        If the list is empty, a ValueError is thrown.
        If the list does not begin with a valid primary, a CommandParseError is thrown.
        """
        if not tokens:
            raise ValueError("tokens is empty")

        name = eat_token(tokens, OperandTokens.OPERAND_NAME)
        values = []

        while tokens and tokens[0][0] == OperandTokens.OPERAND_VALUE:
            values.append(eat_token(tokens, OperandTokens.OPERAND_VALUE))
        
        return cls(name, values)

class ASTExpr(NamedTuple):
    value: Union[ASTPrimary, "ASTBinNot", "ASTBinOr"]

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        """
        Consumes tokens from the list to form an expression. Assumes the list starts with a valid expression.
        EBNF: `expr = LPAREN binor RPAREN | binnot | primary`

        If the list is empty, a ValueError is thrown.
        If the list does not begin with a valid expression a CommandParserError is thrown.
        """
        if peek_token(tokens) == OperandTokens.LPAREN:
            eat_token(tokens, OperandTokens.LPAREN)
            value = ASTBinOr.from_tokens(tokens)
            eat_token(tokens, OperandTokens.RPAREN)

            return cls(value)
        if peek_token(tokens) == OperandTokens.NOT:
            return cls(ASTBinNot.from_tokens(tokens))
        else:
            return cls(ASTPrimary.from_tokens(tokens))

class ASTBinNot(NamedTuple):
    expr: ASTExpr

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        eat_token(tokens, OperandTokens.NOT)
        return cls(ASTExpr.from_tokens(tokens))

class ASTBinAnd(NamedTuple):
    """
    Represents a binary AND expression of primaries
    """
    expressions: List[ASTPrimary]

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        expr = [ASTExpr.from_tokens(tokens)]

        while tokens:
            if peek_token(tokens) == OperandTokens.AND:
                tokens.pop(0)
            
            # Additional expressions are optional and '-a' does not have to exist. So, we try to parse an expression.
            # If we encounter an exception, then it's not an expression, so we move on.
            try:
                expr.append(ASTExpr.from_tokens(tokens))
            except Exception:
                break
        
        return cls(expr)

class ASTBinOr(NamedTuple):
    """
    Represents a binary OR expression. 

    Because OR is the expression with the least precidence, it will often be the root of the AST.
    """
    ands: List[ASTBinAnd]

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        rv = [ASTBinAnd.from_tokens(tokens)]

        while tokens and peek_token(tokens) == OperandTokens.OR:
            # Pop the OR token, then parse the expected expression
            tokens.pop(0)

            rv.append(ASTBinAnd.from_tokens(tokens))
        
        return cls(rv)

    
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