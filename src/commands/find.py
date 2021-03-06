from .command import command, CommandParseError
from enum import Enum, unique, auto
from typing import List, Dict, Tuple, Any, NamedTuple, Union
from io import IOBase
from itertools import takewhile
from getopt import getopt
from pathlib import Path
from functools import reduce
import sys
import os
import fnmatch


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


@operand("name")
def op_name(path: Path, pattern: str) -> bool:
    return fnmatch.fnmatch(path.name, pattern)



class ASTPrimary(NamedTuple):
    """
    Represents a primary expression (an operand and an optional number of values that evaluate to a boolean value)
    """
    name: str
    values: List[str]

    def evaluate(self, path: Path):
        return PATH_OPERAND_EVALUATORS[self.name](path, *self.values)

    def size(self):
        return 1

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


class ASTBinNot(NamedTuple):
    expr: Union[ASTPrimary, "ASTBinNot", "ASTBinOr"]

    def evaluate(self, path: Path) -> bool:
        return not self.expr.evaluate(path)
    
    def size(self) -> int:
        return 1 + self.expr.size()

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        """
        Consumes tokesn from the list to form a BinNot. Assumes the list starts with a valid expression.
        EBNF: `expr = NOT expr`

        If the list is empty, a ValueError is thrown.
        If the list does not begin with a valid expression a CommandParserError is thrown.
        """
        eat_token(tokens, OperandTokens.NOT)
        return cls(expr_from_tokens(tokens))


class ASTBinAnd(NamedTuple):
    """
    Represents a binary AND expression of primaries
    """
    expressions: List[Union[ASTPrimary, ASTBinNot, "ASTBinOr"]]

    def evaluate(self, path: Path) -> bool:
        if len(self.expressions) == 1:
            return self.expressions[0].evaluate(path)
        
        return reduce(lambda a, b: a.evaluate(path) & b.evaluate(path), self.expressions)

    def size(self) -> int:
        return 1 + reduce(lambda a, b: a.size() + b.size())

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        """
        Consumes tokens from the list to form an AND expression. Assumes the list starts with a valid expression.
        AND expressions must contain at least one valid expression. Multiple expressions may be separated optionally with '-a'.
        EBNF: `binand = expr {[AND] expr}`

        If tokens is empty, a ValueError is thrown.
        If the list does not begin with a valid expression a CommandParserError is thrown.
        """
        expr = [expr_from_tokens(tokens)]

        while tokens:
            if peek_token(tokens) == OperandTokens.AND:
                tokens.pop(0)

            # Additional expressions are optional and '-a' does not have to exist. So, we try to parse an expression.
            # If we encounter an exception, then it's not an expression, so we move on.
            try:
                expr.append(expr_from_tokens(tokens))
            except Exception:
                break

        return cls(expr)


class ASTBinOr(NamedTuple):
    """
    Represents a binary OR expression.

    Because OR is the expression with the least precidence, it will often be the root of the AST.
    """
    children: List[ASTBinAnd]

    def evaluate(self, path: Path) -> bool:
        """Evaluates the OR expression"""
        if len(self.children) == 1:
            return self.children[0].evaluate(path)

        return reduce(lambda a, b: a.evaluate(path) | b.evaluate(path), self.children)

    def size(self) -> int:
        """Returns the size of the tree"""
        return 1 + reduce(lambda a, b: a.size() + b.size())

    @classmethod
    def from_tokens(cls, tokens: List[Tuple[OperandTokens, str]]):
        """
        Consumes tokens from the list to form an OR expression. OR expressions are composed of at least one AND expression.
        Assumes the list begins with a valid AND expression. Multiple AND expressions must be separated by `-o`.
        EBNF: `binor = binand {OR binand}`

        If tokens is empty, a ValueError is thrown.
        If the list does not begin with a valid AND expression a CommandParserError is thrown.
        """
        rv = [ASTBinAnd.from_tokens(tokens)]

        while tokens and peek_token(tokens) == OperandTokens.OR:
            # Pop the OR token, then parse the expected expression
            tokens.pop(0)

            rv.append(ASTBinAnd.from_tokens(tokens))

        return cls(rv)


def expr_from_tokens(tokens: List[Tuple[OperandTokens, str]]) -> Union[ASTPrimary, ASTBinNot, ASTBinOr]:
    """
    Consumes tokens from the list to form an expression. Assumes the list starts with a valid expression.
    EBNF: `expr = LPAREN binor RPAREN | binnot | primary`

    If the list is empty, a ValueError is thrown.
    If the list does not begin with a valid expression a CommandParserError is thrown.
    """
    if peek_token(tokens) == OperandTokens.LPAREN:
        eat_token(tokens, OperandTokens.LPAREN)
        rv = ASTBinOr.from_tokens(tokens)
        eat_token(tokens, OperandTokens.RPAREN)

        return rv
    if peek_token(tokens) == OperandTokens.NOT:
        return ASTBinNot.from_tokens(tokens)
    else:
        return ASTPrimary.from_tokens(tokens)



def descend(path: Union[Path, List[Path]], tree: Union[None, ASTPrimary, ASTBinNot, ASTBinOr], verbose=False) -> List[Path]:
    """
    Decends the given path. Returns a list of Paths to all files.
    """
    rv = []

    try:
        path_stack = path[:]
    except TypeError:
        path_stack = [path]
    
    i = 0

    # A while loop is used here instead of a for loop so we can iterate over the "stack" while adding items to it
    while i < len(path_stack):
        current_item: Path = path_stack[i]

        if current_item.is_dir():
            path_stack.extend(current_item.iterdir())

            if verbose:
                print(f"Verbose: {str(current_item)} is directory, adding to stack.")
        else:
            evaluation = tree.evaluate(current_item)
            if evaluation:
                rv.append(current_item)
            
            if verbose:
                print(f"Verbose: {str(current_item)} evaluated to {evaluation}")

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

    if verbose:
        print("Verbose: Enabled")

    file_paths = list(map(Path, takewhile(lambda s: s != "!" and s != "(" and not s.startswith("-"), opt[1])))
    operands = opt[1][len(file_paths):]
    operand_tokens = tokenize_operands(operands)
    tree = expr_from_tokens(operand_tokens)

    if verbose:
        print(f"Verbose: paths: {len(file_paths)}, parsed tokens: {len(operand_tokens)}, tree size: {tree.size()}")

    files = descend(file_paths, tree, verbose)
    for f in files:
        print(f, file=f_out)

if __name__ == "__main__":
    quit(find(sys.argv[1:], os.environ, sys.stdin, sys.stdout))
